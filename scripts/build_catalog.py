"""Generador del catálogo CIBA con build atómico, allowlist y anti-symlink.

Uso:
    python scripts/build_catalog.py --src content --out dist
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import traceback
from datetime import date
from pathlib import Path

from lib.area_reader import leer_area
from lib.columnas_reader import leer_columnas
from lib.errors import ValidationError
from lib.media import copiar_media_autorizada, verificar_destino_sin_extranos
from lib.meta_reader import leer_meta
from lib.paths import COLUMNAS_CARPETAS_OFICIALES
from lib.safety import es_ruta_segura, listar_directorios_seguros, iterar_arbol_seguro
from lib.meta_reader import leer_meta
from validate_content import validar


PERMITIDOS_EN_PAGINA = {"index.html"}


def _leer_json(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def _iter_areas(src: Path):
    """Devuelve (letra, area_dir) exactamente una vez por área, sin symlinks."""
    for letra in COLUMNAS_CARPETAS_OFICIALES:
        carpeta_col = src / letra
        if not carpeta_col.is_dir() or carpeta_col.is_symlink():
            continue

        subdirs, _ = listar_directorios_seguros(carpeta_col, f"content/{letra}")

        for area_dir in subdirs:
            yield letra.upper(), area_dir


def _iter_paginas(area_dir: Path):
    subdirs, _ = listar_directorios_seguros(area_dir, str(area_dir.name))

    for pag_dir in subdirs:
        if pag_dir.name == "_paginas":
            continue
        yield pag_dir


def _copiar_paginas_estaticas(src: Path, tmp: Path) -> list[ValidationError]:
    """Publica páginas auxiliares de CIBA sin convertirlas en artículos."""
    errores: list[ValidationError] = []
    raiz = src / "c" / "C1" / "_paginas"

    if not raiz.exists() and not raiz.is_symlink():
        return errores

    ok, motivo = es_ruta_segura(src, raiz)
    if not ok or not raiz.is_dir():
        errores.append(ValidationError("content/c/C1/_paginas", "ruta", motivo or "no es carpeta"))
        return errores

    archivos, errs_walk = iterar_arbol_seguro(raiz)
    errores.extend(errs_walk)

    for archivo in archivos:
        relativo = archivo.relative_to(raiz)
        if archivo.name != "index.html":
            errores.append(ValidationError(str(relativo), "página auxiliar", "solo se permite index.html"))
            continue

        if relativo.parts and relativo.parts[0] == "plataforma":
            destino = tmp / "plataforma" / relativo.parent.relative_to("plataforma")
        else:
            destino = tmp / "c" / "C1" / relativo.parent
        destino.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copy2(archivo, destino / "index.html")
        except OSError as exc:
            errores.append(ValidationError(str(relativo), "página auxiliar", f"copia falló: {exc}"))

    return errores


def _generar_indice_busqueda_alimentos(raiz_publica: Path) -> list[ValidationError]:
    """Genera el índice ligero del buscador desde las fichas completas."""
    errores: list[ValidationError] = []
    ruta_indice = raiz_publica / "assets" / "data" / "alimentos.json"

    if not ruta_indice.is_file():
        return errores

    try:
        indice = _leer_json(ruta_indice)
    except (OSError, json.JSONDecodeError) as exc:
        return [ValidationError("assets/data/alimentos.json", "índice de alimentos", f"no se pudo leer: {exc}")]

    categorias = indice.get("categorias", [])
    if not isinstance(categorias, list):
        return [ValidationError("assets/data/alimentos.json", "categorías", "se esperaba una lista")]

    registros: list[dict] = []

    for categoria in categorias:
        if not isinstance(categoria, dict):
            errores.append(ValidationError("assets/data/alimentos.json", "categoría", "registro inválido"))
            continue

        archivo = categoria.get("archivo")
        slug = categoria.get("slug")
        nombre_categoria = categoria.get("nombre", "")

        if (
            not isinstance(archivo, str)
            or not archivo.startswith("assets/data/alimentos/")
            or not archivo.endswith(".json")
            or ".." in Path(archivo).parts
        ):
            errores.append(ValidationError("assets/data/alimentos.json", "archivo de grupo", "ruta no autorizada"))
            continue

        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]+", slug):
            errores.append(ValidationError("assets/data/alimentos.json", "slug de grupo", "slug ausente o inválido"))
            continue

        ruta_grupo = raiz_publica / archivo

        try:
            grupo = _leer_json(ruta_grupo)
        except (OSError, json.JSONDecodeError) as exc:
            errores.append(ValidationError(archivo, "grupo de alimentos", f"no se pudo leer: {exc}"))
            continue

        alimentos_grupo = grupo.get("alimentos", [])
        if not isinstance(alimentos_grupo, list):
            errores.append(ValidationError(archivo, "alimentos", "se esperaba una lista"))
            continue

        for alimento in alimentos_grupo:
            if not isinstance(alimento, dict):
                errores.append(ValidationError(archivo, "alimento", "registro inválido"))
                continue

            alimento_id = alimento.get("id")
            nombre = alimento.get("nombre")

            if not isinstance(alimento_id, str) or not isinstance(nombre, str):
                errores.append(ValidationError(archivo, "alimento", "falta id o nombre"))
                continue

            registros.append(
                {
                    "id": alimento_id,
                    "nombre": nombre,
                    "categoria": alimento.get("categoria") or nombre_categoria,
                    "resumen": alimento.get("resumen", ""),
                    "nombres_alternativos": alimento.get("nombres_alternativos", []),
                    "palabras_clave": alimento.get("palabras_clave", []),
                    "ruta_publica": f"c/C1/alimentos/{slug}/",
                }
            )

    if errores:
        return errores

    destino = raiz_publica / "assets" / "data" / "alimentos-busqueda.json"

    try:
        destino.write_text(
            json.dumps(
                {"version": 1, "alimentos": registros},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError as exc:
        errores.append(ValidationError("assets/data/alimentos-busqueda.json", "escritura", f"falló: {exc}"))

    return errores


def _preparar(tmp: Path) -> None:
    if tmp.exists():
        shutil.rmtree(tmp)

    (tmp / "data").mkdir(parents=True, exist_ok=True)


def _copiar_assets(repo_raiz: Path, tmp: Path) -> list[ValidationError]:
    """Copia assets/ respetando la seguridad de rutas."""
    errores: list[ValidationError] = []
    assets_src = repo_raiz / "assets"

    if not assets_src.is_dir():
        return errores

    if assets_src.is_symlink():
        errores.append(ValidationError("assets", "carpeta", "es symlink"))
        return errores

    archivos, errs_walk = iterar_arbol_seguro(assets_src)
    errores.extend(errs_walk)

    for f in archivos:
        rel = f.relative_to(assets_src)
        destino = tmp / "assets" / rel
        destino.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copy2(f, destino)
        except OSError as exc:
            errores.append(ValidationError(str(f), "copia", f"falló: {exc}"))

    return errores


def _copiar_pagina_publica(
    origen_pagina: Path,
    destino_pagina: Path,
    fotos_validadas,
    rel_pagina: str,
) -> list[ValidationError]:
    """Copia SOLO index.html y fotos autorizadas. Nada más. Sin symlinks."""
    errores: list[ValidationError] = []

    ok, motivo = es_ruta_segura(origen_pagina, origen_pagina / "index.html")

    if not ok:
        errores.append(ValidationError(rel_pagina, "index.html", motivo))
        return errores

    index_origen = origen_pagina / "index.html"

    if not index_origen.is_file():
        errores.append(ValidationError(rel_pagina, "index.html", "ausente"))
        return errores

    destino_pagina.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copy2(index_origen, destino_pagina / "index.html")
    except OSError as exc:
        errores.append(
            ValidationError(rel_pagina, "index.html", f"copia falló: {exc}")
        )
        return errores

    if fotos_validadas:
        errs_media = copiar_media_autorizada(
            origen_pagina,
            destino_pagina,
            fotos_validadas,
            rel_pagina,
        )
        errores.extend(errs_media)

    permitidos = set(PERMITIDOS_EN_PAGINA) | {
        f.ruta_relativa for f in fotos_validadas
    }

    errs_clean = verificar_destino_sin_extranos(
        destino_pagina,
        permitidos,
        rel_pagina,
    )
    errores.extend(errs_clean)

    return errores


def _asegurar_documento_responsivo(contenido: str) -> str:
    """Asegura que cada página pública tenga estructura HTML y viewport móvil."""

    # Si el archivo es un fragmento HTML, convertirlo en un documento completo.
    # Esto evita que el navegador móvil utilice un ancho de escritorio.
    tiene_html = re.search(
        r"<html\b",
        contenido,
        flags=re.IGNORECASE,
    )

    if not tiene_html:
        contenido = (
            "<!doctype html>\n"
            '<html lang="es">\n'
            "<head>\n"
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "  <title>CIBA</title>\n"
            "</head>\n"
            "<body>\n"
            f"{contenido}\n"
            "</body>\n"
            "</html>\n"
        )
        return contenido

    # Si ya es un documento completo, comprobar si tiene viewport.
    tiene_viewport = re.search(
        r"<meta\b(?=[^>]*\bname\s*=\s*['\"]viewport['\"])[^>]*>",
        contenido,
        flags=re.IGNORECASE,
    )

    if tiene_viewport:
        return contenido

    etiqueta_viewport = (
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
    )

    cierre_head = re.search(
        r"</head\s*>",
        contenido,
        flags=re.IGNORECASE,
    )

    if cierre_head:
        contenido = (
            contenido[:cierre_head.start()]
            + "  "
            + etiqueta_viewport
            + "\n"
            + contenido[cierre_head.start():]
        )
        return contenido

    apertura_html = re.search(
        r"<html\b[^>]*>",
        contenido,
        flags=re.IGNORECASE,
    )

    if apertura_html:
        cabecera = (
            "\n<head>\n"
            '  <meta charset="utf-8">\n'
            f"  {etiqueta_viewport}\n"
            "</head>\n"
        )
        contenido = (
            contenido[:apertura_html.end()]
            + cabecera
            + contenido[apertura_html.end():]
        )

    return contenido


def _conectar_sistema_global(
    archivo_html: Path,
    raiz_publica: Path,
) -> list[ValidationError]:
    """Prepara el documento móvil y añade el módulo global a una página pública."""
    errores: list[ValidationError] = []

    try:
        contenido = archivo_html.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errores.append(
            ValidationError(
                str(archivo_html),
                "integración global",
                f"no se pudo leer: {exc}",
            )
        )
        return errores

    # Preparar primero la estructura HTML y la configuración para móviles.
    contenido = _asegurar_documento_responsivo(contenido)

    # Solo considera integrado el sistema si existe una etiqueta SCRIPT
    # real que cargue ciba-global.js. Los comentarios HTML no cuentan.
    script_cargado = re.search(
        r'<script\b(?=[^>]*\bsrc\s*=\s*["\'][^"\']*ciba-global\.js(?:[?#][^"\']*)?["\'])[^>]*>',
        contenido,
        flags=re.IGNORECASE,
    )

    if script_cargado:
        etiqueta_existente = script_cargado.group(0)
        etiqueta_actualizada = re.sub(
            r'(\bsrc\s*=\s*["\'][^"\']*ciba-global\.js)(?:[?#][^"\']*)?(["\'])',
            r'\1?v=20261110-25\2',
            etiqueta_existente,
            flags=re.IGNORECASE,
        )
        contenido = contenido.replace(etiqueta_existente, etiqueta_actualizada, 1)
        try:
            archivo_html.write_text(contenido, encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errores.append(
                ValidationError(
                    str(archivo_html),
                    "integración global",
                    f"no se pudo guardar: {exc}",
                )
            )
        return errores

    script = raiz_publica / "assets" / "js" / "ciba-global.js"

    if not script.is_file():
        errores.append(
            ValidationError(
                str(archivo_html),
                "integración global",
                "no existe assets/js/ciba-global.js en la publicación",
            )
        )
        return errores

    ruta_relativa = Path(
        os.path.relpath(script, archivo_html.parent)
    ).as_posix()

    etiqueta = (
        f'<script type="module" src="{ruta_relativa}" '
        'data-ciba-global-script></script>'
    )

    cierre = re.search(r"</body\s*>", contenido, flags=re.IGNORECASE)

    if cierre:
        contenido = (
            contenido[:cierre.start()]
            + etiqueta
            + "\n"
            + contenido[cierre.start():]
        )
    else:
        contenido += "\n" + etiqueta + "\n"

    try:
        archivo_html.write_text(contenido, encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errores.append(
            ValidationError(
                str(archivo_html),
                "integración global",
                f"no se pudo guardar: {exc}",
            )
        )

    return errores


def _construir_en_tmp(
    src: Path,
    tmp: Path,
    hoy: date | None,
) -> list[ValidationError]:

    errores: list[ValidationError] = []

    esquema = src / "_esquema"

    columnas_cfg, errs_cols = leer_columnas(
        esquema / "columnas.json",
        "content/_esquema/columnas.json",
    )
    errores.extend(errs_cols)

    if columnas_cfg is None:
        return errores

    areas_registradas: list[dict] = []
    paginas_publicadas: list[dict] = []

    for letra, area_dir in _iter_areas(src):
        rel_area = str(area_dir.relative_to(src))

        area_meta, errs_area = leer_area(
            area_dir / "area.json",
            rel_area,
        )
        errores.extend(errs_area)

        if area_meta is None:
            continue

        index_area = area_dir / "index.html"

        if index_area.exists() or index_area.is_symlink():
            destino_area = tmp / f"{letra.lower()}/{area_dir.name}"

            errs_copia_area = _copiar_pagina_publica(
                area_dir,
                destino_area,
                [],
                rel_area,
            )
            errores.extend(errs_copia_area)

        areas_registradas.append(
            {
                **area_meta.datos,
                "ruta_publica": f"{letra.lower()}/{area_dir.name}/",
            }
        )

        for pag_dir in _iter_paginas(area_dir):
            rel_pag = str(pag_dir.relative_to(src))

            pagina, errs_pag = leer_meta(
                pag_dir / "meta.json",
                rel_pag,
                hoy=hoy,
            )
            errores.extend(errs_pag)

            if pagina is None:
                continue

            if pagina.datos.get("estado") != "publicado":
                continue

            registro = {
                **pagina.datos,
                "ruta_publica": (
                    f"{letra.lower()}/{area_dir.name}/{pag_dir.name}/"
                ),
            }

            paginas_publicadas.append(registro)

            destino_pagina = tmp / registro["ruta_publica"]

            errs_copia = _copiar_pagina_publica(
                pag_dir,
                destino_pagina,
                pagina.fotos_validadas,
                rel_pag,
            )
            errores.extend(errs_copia)

    if errores:
        return errores

    catalogo = {
        "version": 1,
        "generado": (hoy or date.today()).isoformat(),
        "columnas": columnas_cfg.columnas,
        "areas": sorted(
            areas_registradas,
            key=lambda a: (
                a.get("columna", ""),
                a.get("orden", 0),
                a.get("id", ""),
            ),
        ),
        "paginas": sorted(
            paginas_publicadas,
            key=lambda p: (
                p.get("columna", ""),
                p.get("area", ""),
                p.get("id", ""),
            ),
        ),
    }

    (tmp / "data" / "catalogo.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (tmp / "data" / "columnas.json").write_text(
        json.dumps(columnas_cfg.datos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (tmp / "data" / "areas.json").write_text(
        json.dumps(
            {
                "version": 1,
                "areas": catalogo["areas"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # La portada del sitio también forma parte del artefacto público.
    portada = src.parent / "index.html"

    if portada.exists() or portada.is_symlink():
        ok, motivo = es_ruta_segura(src.parent, portada)

        if not ok:
            errores.append(
                ValidationError("index.html", "portada", motivo)
            )
        elif not portada.is_file():
            errores.append(
                ValidationError("index.html", "portada", "no es archivo")
            )
        else:
            try:
                shutil.copy2(portada, tmp / "index.html")
            except OSError as exc:
                errores.append(
                    ValidationError(
                        "index.html",
                        "portada",
                        f"copia fallida: {exc}",
                    )
                )

    # Copiar los recursos compartidos del proyecto.
    errs_assets = _copiar_assets(src.parent, tmp)
    errores.extend(errs_assets)

    # Generar índice ligero del buscador a partir de las fichas fuente.
    errores.extend(_generar_indice_busqueda_alimentos(tmp))

    # Páginas auxiliares (bibliotecas y herramientas) fuera del catálogo editorial.
    errores.extend(_copiar_paginas_estaticas(src, tmp))

    if errores:
        return errores

    # El sistema global es opcional para los entornos de prueba.
    # En el sitio real se integra cuando existen AMBOS recursos.
    script_global = tmp / "assets" / "js" / "ciba-global.js"
    css_global = tmp / "assets" / "css" / "ciba-global.css"

    sistema_global_disponible = (
        script_global.is_file() and css_global.is_file()
    )

    if sistema_global_disponible:
        # Incorporar el menú, el buscador y la configuración móvil
        # a todas las páginas generadas, incluida la portada.
        paginas_html = sorted(tmp.rglob("index.html"))

        for archivo_html in paginas_html:
            errs_global = _conectar_sistema_global(
                archivo_html,
                tmp,
            )
            errores.extend(errs_global)

        # Refuerzo final: versionar todas las referencias del módulo global
        # después de copiar portada y páginas auxiliares al artefacto.
        for archivo_html in tmp.rglob("*.html"):
            try:
                html = archivo_html.read_text(encoding="utf-8")

                # Identidad verbal única: toda firma o lema asociado a CIBA
                # utiliza exclusivamente el lema institucional vigente.
                sustituciones_identidad = (
                    ("CRECER · CONECTAR · ACOMPAÑAR", "CRECEMOS ACOMPAÑÁNDONOS"),
                    ("CRECER · CONECTAR · ACOMPAÑAR.", "CRECEMOS ACOMPAÑÁNDONOS."),
                    ("Crecer · Conectar · Acompañar", "Crecemos acompañándonos"),
                    ("Un espacio para crecer, conectar y acompañar.", "Un espacio donde crecemos acompañándonos."),
                    ("Un espacio para crecer, conectar y acompañar", "Un espacio donde crecemos acompañándonos"),
                    ("Crecer, conectar y acompañar.", "Crecemos acompañándonos."),
                    ("crecer, conectar y acompañar", "crecemos acompañándonos"),
                    ("Un proyecto para crecer acompañándonos.", "Crecemos acompañándonos."),
                    ("CIBA · Crecer · Conectar · Acompañar", "CIBA · Crecemos acompañándonos"),
                    ("CIBA · Conocimiento, confianza y acompañamiento", "CIBA · Crecemos acompañándonos"),
                    ("CIBA · Crecer, conectar y acompañar", "CIBA · Crecemos acompañándonos"),
                )
                html_actualizado = html
                for texto_anterior, texto_nuevo in sustituciones_identidad:
                    html_actualizado = html_actualizado.replace(texto_anterior, texto_nuevo)

                html_actualizado = re.sub(
                    r'(<script\b[^>]*\bsrc\s*=\s*["\'][^"\']*ciba-global\.js)(?:[?#][^"\']*)?(["\'][^>]*>)',
                    r'\1?v=20261110-20\2',
                    html,
                    flags=re.IGNORECASE,
                )
                html_actualizado = re.sub(
                    r'(<script\b[^>]*\bsrc\s*=\s*["\'][^"\']*ciba-plataforma\.js)(?:[?#][^"\']*)?(["\'][^>]*>)',
                    r'\1?v=20261110-24\2',
                    html_actualizado,
                    flags=re.IGNORECASE,
                )
                if html_actualizado != html:
                    archivo_html.write_text(html_actualizado, encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                errores.append(
                    ValidationError(
                        str(archivo_html),
                        "versionado del sistema global",
                        f"no se pudo actualizar: {exc}",
                    )
                )

    return errores


def _instalar_atomico(tmp: Path, out: Path) -> list[str]:
    errores: list[str] = []
    backup = out.parent / (out.name + ".old")

    if backup.exists():
        shutil.rmtree(backup)

    tenia_anterior = out.exists()

    if tenia_anterior:
        os.replace(out, backup)

    try:
        os.replace(tmp, out)
    except OSError as exc:
        errores.append(f"fallo al instalar dist/: {exc}")

        if tenia_anterior and backup.exists() and not out.exists():
            try:
                os.replace(backup, out)
                errores.append("dist/ anterior restaurado desde backup")
            except OSError as exc2:
                errores.append(
                    f"CRÍTICO: no se pudo restaurar dist/: {exc2}"
                )

        return errores

    if not (out / "data" / "catalogo.json").is_file():
        errores.append(
            "instalación verificada fallida: catalogo.json no presente"
        )

        if tenia_anterior and backup.exists():
            shutil.rmtree(out, ignore_errors=True)

            try:
                os.replace(backup, out)
                errores.append("dist/ anterior restaurado desde backup")
            except OSError as exc3:
                errores.append(
                    f"CRÍTICO: no se pudo restaurar dist/: {exc3}"
                )

        return errores

    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)

    return errores


def construir(
    src: Path,
    out: Path,
    *,
    hoy: date | None = None,
) -> int:

    errores = validar(src, hoy=hoy)

    if errores:
        for e in errores:
            print(e, file=sys.stderr)

        print(
            f"\n{len(errores)} error(es). "
            "No se genera catálogo; dist/ anterior intacto.",
            file=sys.stderr,
        )
        return 1

    tmp = out.parent / (out.name + ".tmp")
    _preparar(tmp)

    try:
        errs_build = _construir_en_tmp(src, tmp, hoy)

    except Exception as exc:  # noqa: BLE001
        print(f"ERROR de build: {exc}", file=sys.stderr)
        traceback.print_exc()
        shutil.rmtree(tmp, ignore_errors=True)
        print("dist/ anterior conservado.", file=sys.stderr)
        return 1

    if errs_build:
        for e in errs_build:
            print(e, file=sys.stderr)

        shutil.rmtree(tmp, ignore_errors=True)
        print("dist/ anterior conservado.", file=sys.stderr)
        return 1

    errs_install = _instalar_atomico(tmp, out)

    if errs_install:
        for e in errs_install:
            print(e, file=sys.stderr)

        return 1

    print(
        f"OK: catálogo en {out}/data/catalogo.json "
        f"({len(_leer_json(out / 'data' / 'catalogo.json')['paginas'])} "
        "páginas publicadas)."
    )

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera el catálogo CIBA."
    )
    parser.add_argument("--src", default="content", type=Path)
    parser.add_argument("--out", default="dist", type=Path)

    args = parser.parse_args(argv)

    return construir(args.src, args.out)


if __name__ == "__main__":
    raise SystemExit(main())