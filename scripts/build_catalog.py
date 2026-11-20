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
from html import escape as html_escape
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
MAX_IMAGEN_BYTES = 500 * 1024
MAX_PDF_BYTES = 2 * 1024 * 1024
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}


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
    """Recorre páginas directas y páginas dentro de contenedores archivados.

    Una subsección con estado 'archivado' funciona como contenedor editorial:
    no se publica como artículo, pero permite alojar artículos anidados.
    """
    def recorrer(padre: Path):
        subdirs, _ = listar_directorios_seguros(padre, str(padre))
        for pag_dir in subdirs:
            if pag_dir.name == "_paginas":
                continue
            yield pag_dir
            meta_path = pag_dir / "meta.json"
            if meta_path.is_file() and not meta_path.is_symlink():
                try:
                    datos = _leer_json(meta_path)
                except (OSError, json.JSONDecodeError):
                    datos = {}
                if datos.get("estado") == "archivado":
                    yield from recorrer(pag_dir)

    yield from recorrer(area_dir)


def _copiar_indices_columnas(src: Path, tmp: Path) -> list[ValidationError]:
    """Publica la portada editorial de cada columna en su raíz /c/, /i/, /b/ o /a/."""
    errores: list[ValidationError] = []
    for letra in ("c", "i", "b", "a"):
        origen = src / letra / "index.html"
        if not origen.exists() and not origen.is_symlink():
            continue
        ok, motivo = es_ruta_segura(src, origen)
        if not ok or not origen.is_file():
            errores.append(ValidationError(f"{letra}/index.html", "portada de columna", motivo or "no es archivo"))
            continue
        destino = tmp / letra / "index.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(origen, destino)
        except OSError as exc:
            errores.append(ValidationError(f"{letra}/index.html", "portada de columna", f"copia fallida: {exc}"))
    return errores


def _copiar_paginas_estaticas(src: Path, tmp: Path) -> list[ValidationError]:
    """Publica páginas auxiliares de CIBA en la columna editorial que les corresponde."""
    errores: list[ValidationError] = []
    raices = (
        (src / "c" / "C1" / "_paginas", Path("c") / "C1"),
        (src / "b" / "B4" / "B4-02" / "_paginas", Path("b") / "B4" / "B4-02"),
    )

    for raiz, prefijo_destino in raices:
        if not raiz.exists() and not raiz.is_symlink():
            continue

        rel_raiz = raiz.relative_to(src).as_posix()
        ok, motivo = es_ruta_segura(src, raiz)
        if not ok or not raiz.is_dir():
            errores.append(ValidationError(rel_raiz, "ruta", motivo or "no es carpeta"))
            continue

        archivos, errs_walk = iterar_arbol_seguro(raiz)
        errores.extend(errs_walk)

        for archivo in archivos:
            relativo = archivo.relative_to(raiz)
            if archivo.name != "index.html":
                errores.append(ValidationError(str(relativo), "página auxiliar", "solo se permite index.html"))
                continue

            if prefijo_destino == Path("c") / "C1" and relativo.parts and relativo.parts[0] == "plataforma":
                destino = tmp / "plataforma" / relativo.parent.relative_to("plataforma")
            else:
                destino = tmp / prefijo_destino / relativo.parent
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
        if f.suffix.lower() in EXTENSIONES_IMAGEN:
            peso = f.stat().st_size
            if peso > MAX_IMAGEN_BYTES:
                errores.append(ValidationError(
                    str(rel),
                    "peso de imagen",
                    f"{peso / 1024:.1f} KB; supera el límite CIBA de 500 KB",
                ))
                continue
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

    # Publicar únicamente PDF locales, seguros y reconocibles. El builder
    # nunca copia documentos arbitrarios: limita extensión, tamaño, ruta y firma.
    archivos_pagina, errs_walk_pdf = iterar_arbol_seguro(origen_pagina)
    errores.extend(errs_walk_pdf)
    pdf_permitidos: set[str] = set()
    for archivo in archivos_pagina:
        if archivo.suffix.lower() != ".pdf":
            continue
        relativo = archivo.relative_to(origen_pagina).as_posix()
        ok_pdf, motivo_pdf = es_ruta_segura(origen_pagina, archivo)
        if not ok_pdf:
            errores.append(ValidationError(rel_pagina, "PDF", f"ruta insegura: {motivo_pdf}"))
            continue
        try:
            peso_pdf = archivo.stat().st_size
            with archivo.open("rb") as entrada:
                firma_pdf = entrada.read(5)
        except OSError as exc:
            errores.append(ValidationError(rel_pagina, "PDF", f"no se pudo leer: {exc}"))
            continue
        if peso_pdf == 0 or peso_pdf > MAX_PDF_BYTES:
            errores.append(ValidationError(
                str(Path(rel_pagina) / relativo),
                "peso de PDF",
                f"{peso_pdf / 1024:.1f} KB; debe ser mayor que 0 y no superar 2048 KB",
            ))
            continue
        if firma_pdf != b"%PDF-":
            errores.append(ValidationError(
                str(Path(rel_pagina) / relativo),
                "formato PDF",
                "el archivo no contiene la firma PDF válida",
            ))
            continue
        destino_pdf = destino_pagina / relativo
        destino_pdf.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(archivo, destino_pdf)
            pdf_permitidos.add(relativo)
        except OSError as exc:
            errores.append(ValidationError(rel_pagina, "copia PDF", f"falló: {exc}"))

    if fotos_validadas:
        # En la serie de Lactancia (C1-16 a C1-40), ninguna imagen local
        # puede superar 200 KB: prioridad a conexiones lentas y móviles.
        match_lactancia = re.search(r"(?:^|/)C1-(\d+)(?:/|$)", rel_pagina)
        es_lactancia = bool(match_lactancia and 16 <= int(match_lactancia.group(1)) <= 40)
        if es_lactancia:
            for foto in fotos_validadas:
                ruta_foto = origen_pagina / foto.ruta_relativa
                try:
                    peso_foto = ruta_foto.stat().st_size
                except OSError as exc:
                    errores.append(ValidationError(rel_pagina, "imagen de lactancia", f"no se pudo comprobar el peso: {exc}"))
                    continue
                if peso_foto > 200 * 1024:
                    errores.append(ValidationError(
                        str(Path(rel_pagina) / foto.ruta_relativa),
                        "peso de imagen en Lactancia",
                        f"{peso_foto / 1024:.1f} KB; el máximo permitido es 200 KB",
                    ))
        errs_media = copiar_media_autorizada(
            origen_pagina,
            destino_pagina,
            fotos_validadas,
            rel_pagina,
        )
        errores.extend(errs_media)

    permitidos = set(PERMITIDOS_EN_PAGINA) | pdf_permitidos | {
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




def _normalizar_migas_y_metadatos(
    contenido: str,
    archivo_html: Path,
    raiz_publica: Path,
    catalogo: dict | None,
) -> str:
    """Unifica SEO y ruta de navegación sin modificar el cuerpo editorial."""
    if not isinstance(catalogo, dict):
        return contenido
    try:
        partes = archivo_html.relative_to(raiz_publica).parts
    except ValueError:
        return contenido
    if len(partes) < 2 or partes[0] not in ("c", "i", "b", "a") or partes[-1] != "index.html":
        return contenido

    letra = partes[0]
    ruta = "/".join(partes[:-1]) + "/"
    columnas = catalogo.get("columnas", [])
    areas = catalogo.get("areas", [])
    subsecciones = catalogo.get("subsecciones", [])
    paginas = catalogo.get("paginas", [])
    columna = next((x for x in columnas if str(x.get("id", "")).lower() == letra), None)
    if not columna:
        return contenido

    area = next((x for x in areas if x.get("ruta_publica") == f"{letra}/{partes[1]}/"), None) if len(partes) >= 3 else None
    subseccion = next((x for x in subsecciones if x.get("ruta_publica") == ruta), None)
    pagina = next((x for x in paginas if x.get("ruta_publica") == ruta), None)
    if ruta == f"{letra}/":
        nivel, registro = "columna", columna
    elif area and ruta == area.get("ruta_publica"):
        nivel, registro = "seccion", area
    elif subseccion:
        nivel, registro = "subseccion", subseccion
    elif pagina:
        nivel, registro = "articulo", pagina
    else:
        return contenido

    paleta = _paleta_columna(letra)
    titulo = str(registro.get("titulo", columna.get("titulo", "CIBA"))).strip()
    descripcion = str(registro.get("descripcion", columna.get("descripcion", ""))).strip()
    nombre_columna = str(columna.get("titulo", paleta["nombre"])).strip()
    titulo_html = html_escape(f"{titulo} | CIBA" if nivel == "columna" else f"{titulo} | {nombre_columna} · CIBA")
    descripcion_html = html_escape(descripcion, quote=True)
    color_html = html_escape(paleta["oscuro"], quote=True)

    def reemplazar_meta(nombre: str, etiqueta: str) -> None:
        nonlocal contenido
        patron = re.compile(
            rf"<meta\b(?=[^>]*\bname\s*=\s*['\"]{re.escape(nombre)}['\"])[^>]*>",
            re.IGNORECASE,
        )
        if patron.search(contenido):
            contenido = patron.sub(etiqueta, contenido, count=1)
        else:
            cierre = re.search(r"</head\s*>", contenido, re.IGNORECASE)
            if cierre:
                contenido = contenido[:cierre.start()] + etiqueta + "\n" + contenido[cierre.start():]

    patron_title = re.compile(r"<title\b[^>]*>[\s\S]*?</title\s*>", re.IGNORECASE)
    if patron_title.search(contenido):
        contenido = patron_title.sub(f"<title>{titulo_html}</title>", contenido, count=1)
    else:
        cierre = re.search(r"</head\s*>", contenido, re.IGNORECASE)
        if cierre:
            contenido = contenido[:cierre.start()] + f"<title>{titulo_html}</title>\n" + contenido[cierre.start():]
    reemplazar_meta("description", f'<meta name="description" content="{descripcion_html}">')
    reemplazar_meta("theme-color", f'<meta name="theme-color" content="{color_html}">')

    # Reemplazar cualquier migas heredada por una ruta canónica. Conservar
    # una ruta antigua impedía corregir jerarquías y duplicaba estilos.
    contenido = re.sub(
        r'<style\b(?=[^>]*\bdata-ciba-migas-style(?:\s|=|>))[^>]*>[\s\S]*?</style\s*>',
        '',
        contenido,
        flags=re.IGNORECASE,
    )
    patron_migas_existentes = re.compile(
        r'<(?P<tag>nav|div|ol|ul)\b'
        r'(?=[^>]*\bclass\s*=\s*["\'][^"\']*(?:breadcrumb|ciba-migas|migas|ruta-navegacion)[^"\']*["\'])'
        r'[^>]*>[\s\S]*?</(?P=tag)\s*>',
        re.IGNORECASE,
    )
    contenido = patron_migas_existentes.sub('', contenido)

    items: list[tuple[str, str | None]] = [("CIBA", "index.html")]
    if nivel == "columna":
        items.append((titulo, None))
    else:
        items.append((nombre_columna, f"{letra}/index.html"))
    if nivel in ("seccion", "subseccion", "articulo") and area:
        items.append((str(area.get("titulo", area.get("id", "Sección"))), f"{area['ruta_publica']}index.html"))
    if nivel == "articulo":
        padres = [
            x for x in subsecciones
            if str(pagina.get("ruta_publica", "")).startswith(str(x.get("ruta_publica", "")))
        ]
        if padres:
            padre = max(padres, key=lambda x: len(str(x.get("ruta_publica", ""))))
            items.append((str(padre.get("titulo", padre.get("id", "Subsección"))), f"{padre['ruta_publica']}index.html"))
    if nivel != "columna":
        items.append((titulo, None))

    enlaces: list[str] = []
    for etiqueta, destino in items:
        if destino is None:
            enlaces.append('<span aria-current="page">' + html_escape(etiqueta) + '</span>')
        else:
            href = os.path.relpath(raiz_publica / destino, archivo_html.parent).replace(os.sep, "/")
            enlaces.append('<a href="' + html_escape(href, quote=True) + '">' + html_escape(etiqueta) + '</a>')
    nav = (
        '<nav class="ciba-migas" data-ciba-migas aria-label="Ruta de navegación">'
        + '<span class="ciba-migas-lista">' + '<span class="ciba-migas-sep">›</span>'.join(enlaces) + '</span>'
        + '</nav>'
    )
    estilos = f"""<style data-ciba-migas-style>
.ciba-migas{{position:relative;z-index:4;padding:11px max(18px,calc((100% - 1120px)/2));background:{paleta['fondo']};border-bottom:1px solid #00000012;color:{paleta['tinta']};font:11px/1.5 Arial,Helvetica,sans-serif}}
.ciba-migas-lista{{display:flex;align-items:center;flex-wrap:wrap;gap:8px}}
.ciba-migas a{{color:{paleta['medio']};font-weight:700;text-decoration:none}}
.ciba-migas a:hover{{text-decoration:underline}}
.ciba-migas-sep{{color:{paleta['medio']};opacity:.7}}
.ciba-migas [aria-current="page"]{{font-weight:700}}
</style>"""
    cierre_head = re.search(r"</head\\s*>", contenido, re.IGNORECASE)
    if cierre_head:
        antes_head = contenido[:cierre_head.start()].rstrip()
        contenido = antes_head + estilos + "\\n" + contenido[cierre_head.start():]
    apertura_body = re.search(r"<body\\b[^>]*>", contenido, re.IGNORECASE)
    if apertura_body:
        despues_body = contenido[apertura_body.end():].lstrip()
        contenido = contenido[:apertura_body.end()] + "\\n" + nav + "\\n" + despues_body
    return contenido


def _normalizar_estilo_informatica(contenido: str, archivo_html: Path, raiz_publica: Path) -> str:
    """Unifica la identidad azul de las páginas interiores de INFORMÁTICA.

    La portada principal conserva su diseño propio y actúa como referencia visual.
    Los artículos y páginas temáticas mantienen intactos sus recursos y estructura.
    """
    try:
        partes = archivo_html.relative_to(raiz_publica).parts
    except ValueError:
        return contenido
    if len(partes) < 3 or partes[0].lower() != "i" or partes[-1].lower() != "index.html":
        return contenido
    if "data-ciba-informatica-unificacion" in contenido:
        return contenido

    estilos = """<style data-ciba-informatica-unificacion>
:root {
  --blue:#287b9a !important; --azul:#287b9a !important;
  --deep:#12364d !important; --noche:#12364d !important;
  --ink:#273943 !important; --tinta:#273943 !important;
  --muted:#63747c !important; --suave:#63747c !important;
  --cream:#f5f3ec !important; --crema:#f5f3ec !important;
  --paper:#fffefa !important; --papel:#fffefa !important;
  --line:#dce5e8 !important; --borde:#dce5e8 !important;
  --gold:#d5b879 !important; --oro:#d5b879 !important;
}
body { background:#f5f3ec !important; color:#273943 !important; }
a { color:#176783; text-underline-offset:3px; }
.hero {
  padding:62px 0 54px !important; color:#fff !important;
  background:
    radial-gradient(circle at 78% 22%,rgba(67,142,170,.32),transparent 34%),
    linear-gradient(120deg,#12364d 0%,#174f70 58%,#206b88 100%) !important;
}
.hero h1 { color:#fff !important; font-family:Georgia,"Times New Roman",serif !important; font-weight:400 !important; letter-spacing:-.035em !important; }
.hero p,.hero .lead { color:#e5eff3 !important; }
.kicker,.hero .kicker { color:#e9d6ad !important; }
.eyebrow,.tag { color:#287b9a !important; }
.wrap { width:min(1060px,calc(100% - 36px)) !important; margin-inline:auto !important; }
nav.toc,.article-nav {
  background:rgba(255,254,250,.94) !important;
  border-bottom:1px solid #dce5e8 !important;
  backdrop-filter:blur(12px);
}
nav.toc a,.article-nav a { color:#12364d !important; }
.block h2,.article h2,main h2 { color:#12364d !important; }
.block h3,.article h3,main h3 { color:#176783 !important; }
.card,.tile,.figure,.infographic {
  background:#fffefa !important; border-color:#dce5e8 !important;
  border-radius:12px !important;
}
.callout,.note { border-color:#438eaa !important; }
.article-footer,footer { background:#12364d !important; color:#e5eff3 !important; }
.article-footer a,footer a { color:#d5b879 !important; }
:focus-visible { outline-color:#287b9a; outline-offset:3px; }
body { font-family:Arial,Helvetica,sans-serif !important; line-height:1.75; }
h1,h2,h3,h4 { font-family:Georgia,"Times New Roman",serif !important; line-height:1.2; }
.hero h1, .hero h2, .hero h3 { color:#fff !important; }
.hero p, .hero .lead { color:#e5eff3 !important; }
:where(.grid,.grid2,.resources,.steps,.flow,.pillars,.alertlist) { min-width:0; }
:where(.card,.tile,.resource,.step,.pillar,.interactive,.quiz,.scenario,.check,.checklist,.figure,.infographic,.callout,.note,.alert) {
  max-width:100%; border-color:#dce5e8;
}
:where(.card,.tile,.resource,.step,.pillar,.interactive,.quiz,.scenario,.check,.checklist) {
  border-radius:12px;
}
:where(.card,.tile,.resource,.step,.pillar) { background:#fffefa; }
:where(.card h3,.tile h3,.resource h3,.interactive h3,.quiz h3,.scenario h3) { color:#12364d !important; }
:where(.card p,.tile p,.resource p,.note,figcaption) { color:#63747c; }
:where(.callout,.note,.interactive,.quiz,.scenario,.check,.checklist,.figure,.infographic) {
  border-color:#b9dce9;
}
:where(button,.btn,.action,.boton,input[type="button"],input[type="submit"]) {
  min-height:44px; font:inherit; cursor:pointer;
}
:where(button,.btn,.action,.boton) {
  border-radius:8px; background:#174f70; color:#fff;
}
:where(input,select,textarea) {
  max-width:100%; min-height:44px; border-color:#b9cbd2;
}
:where(audio,video,iframe,canvas,svg,img) { max-width:100%; }
audio,video,iframe { width:auto; }
img,video { height:auto; }
table { max-width:100%; }
@media (max-width:700px) {
  .wrap { width:min(100% - 28px,1060px) !important; }
  :where(.grid,.grid2,.resources,.steps,.flow,.pillars) { grid-template-columns:minmax(0,1fr) !important; }
  :where(button,.btn,.action,.boton) { min-height:44px; }
  table { display:block; overflow-x:auto; }
}
@media (prefers-reduced-motion:reduce) {
  *,*::before,*::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; }
}
@media (max-width:700px) {
  .hero { padding:46px 0 42px !important; }
  .wrap { width:min(100% - 28px,1060px) !important; }
}
</style>"""
    cierre = re.search(r"</body\s*>", contenido, flags=re.IGNORECASE)
    if cierre:
        contenido = contenido[:cierre.start()] + estilos + "\n" + contenido[cierre.start():]
    else:
        contenido += "\n" + estilos
    return contenido


def _normalizar_sistema_editorial(contenido: str, archivo_html: Path, raiz_publica: Path) -> str:
    """Aplica el sistema tipográfico y los componentes comunes sin borrar la identidad cromática."""
    try:
        partes = archivo_html.relative_to(raiz_publica).parts
    except ValueError:
        return contenido
    if len(partes) < 2 or partes[0].lower() not in ("c", "i", "b", "a") or partes[-1].lower() != "index.html":
        return contenido
    if "data-ciba-sistema-editorial" in contenido:
        return contenido

    paleta = _paleta_columna(partes[0])
    estilos = f"""<style data-ciba-sistema-editorial>
:root {{
  --ciba-color-primario: {paleta['oscuro']};
  --ciba-color-secundario: {paleta['medio']};
  --ciba-color-acento: {paleta['acento']};
  --ciba-color-fondo: {paleta['fondo']};
  --ciba-color-papel: {paleta['papel']};
  --ciba-color-texto: {paleta['tinta']};
  --ciba-font-display: Georgia, "Times New Roman", serif;
  --ciba-font-body: Arial, Helvetica, sans-serif;
  --ciba-texto-base: 16px;
  --ciba-linea-base: 1.75;
}}
body {{
  font-family: var(--ciba-font-body);
  font-size: var(--ciba-texto-base);
  line-height: var(--ciba-linea-base);
  -webkit-text-size-adjust: 100%;
}}
h1, h2, h3, h4 {{
  font-family: var(--ciba-font-display);
  line-height: 1.2;
  text-wrap: balance;
}}
p, li {{ line-height: var(--ciba-linea-base); }}
img, video, iframe, svg {{ max-width: 100%; }}
img, video {{ height: auto; }}
:where(button, input, select, textarea) {{ font: inherit; }}
:where(button, a, input, select, textarea, summary) {{ -webkit-tap-highlight-color: transparent; }}
:where(button, a, input, select, textarea, summary):focus-visible {{
  outline: 3px solid var(--ciba-color-acento);
  outline-offset: 3px;
}}
.ciba-estandar-kicker {{
  color: var(--ciba-color-secundario);
  font: 800 10px/1.4 var(--ciba-font-body);
  letter-spacing: .16em;
  text-transform: uppercase;
}}
.ciba-estandar-tarjeta {{
  min-width: 0;
  padding: clamp(18px, 3vw, 26px);
  border: 1px solid color-mix(in srgb, var(--ciba-color-primario) 14%, transparent);
  border-radius: 12px;
  background: var(--ciba-color-papel);
  color: var(--ciba-color-texto);
  box-shadow: 0 8px 24px rgba(0,0,0,.055);
}}
.ciba-estandar-nota {{
  padding: clamp(18px, 3vw, 26px);
  border-left: 4px solid var(--ciba-color-acento);
  background: var(--ciba-color-papel);
  color: var(--ciba-color-texto);
}}
.ciba-estandar-boton {{
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--ciba-color-primario);
  border-radius: 8px;
  background: var(--ciba-color-primario);
  color: #fff;
  font-weight: 700;
  text-decoration: none;
}}
.ciba-estandar-migas {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font: 12px/1.5 var(--ciba-font-body);
}}
.ciba-estandar-migas a {{ color: var(--ciba-color-secundario); }}
@media (max-width: 640px) {{
  body {{ font-size: 16px; }}
  :where(button, .ciba-estandar-boton) {{ min-height: 44px; }}
  table {{ font-size: 14px; }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    scroll-behavior: auto !important;
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }}
}}
</style>"""
    cierre = re.search(r"</body\s*>", contenido, flags=re.IGNORECASE)
    if cierre:
        contenido = contenido[:cierre.start()] + estilos + "\n" + contenido[cierre.start():]
    else:
        contenido += "\n" + estilos
    return contenido




def _normalizar_crianza(contenido: str, archivo_html: Path, raiz_publica: Path) -> str:
    """Estandariza la presentación interior de CRIANZA sin alterar su contenido ni sus medios."""
    try:
        partes = archivo_html.relative_to(raiz_publica).parts
    except ValueError:
        return contenido
    if len(partes) < 2 or partes[0].lower() != "c" or partes[-1].lower() != "index.html":
        return contenido
    if "data-ciba-crianza-estandar" in contenido:
        return contenido

    estilos = """<style data-ciba-crianza-estandar>
:root {
  --ciba-crianza-noche: #172b27;
  --ciba-crianza-verde: #526e56;
  --ciba-crianza-tierra: #a9583e;
  --ciba-crianza-oro: #d9b878;
  --ciba-crianza-marfil: #f5f0e5;
  --ciba-crianza-papel: #fffdf7;
  --ciba-crianza-tinta: #29332d;
  --ciba-crianza-suave: #73776d;
  --ciba-crianza-linea: #e4ddcf;
}
body {
  background-color: var(--ciba-crianza-marfil);
  color: var(--ciba-crianza-tinta);
  font-family: Arial, Helvetica, sans-serif;
  font-size: 16px;
  line-height: 1.75;
}
h1, h2, h3, h4 {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.2;
  text-wrap: balance;
}
a { text-underline-offset: 3px; }
a:focus-visible, button:focus-visible, input:focus-visible,
select:focus-visible, textarea:focus-visible, summary:focus-visible {
  outline: 3px solid var(--ciba-crianza-oro);
  outline-offset: 3px;
}
.hero, .cabecera-articulo {
  color: #fffdf7;
  border-bottom: 3px solid var(--ciba-crianza-verde);
}
.hero h1, .cabecera-articulo h1 {
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 400;
  line-height: 1.12;
  text-wrap: balance;
}
.hero p, .cabecera-articulo .bajada, .hero-descripcion {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 15px;
  line-height: 1.85;
}
.tag, .kicker, .eyebrow, .sobrelinea, .etiqueta {
  letter-spacing: .16em;
}
.ciba-articulo {
  box-sizing: border-box;
  width: min(100% - 36px, 960px);
  margin: 28px auto 58px;
  padding: clamp(20px, 4vw, 48px);
  border: 1px solid var(--ciba-crianza-linea);
  border-top: 4px solid var(--ciba-crianza-verde);
  border-radius: 14px;
  background: var(--ciba-crianza-papel);
  color: var(--ciba-crianza-tinta);
  font-family: Arial, Helvetica, sans-serif;
  font-size: 16px;
  line-height: 1.8;
  box-shadow: 0 10px 30px rgba(23,43,39,.055);
}
.ciba-articulo h2, .articulo h2 {
  color: var(--ciba-crianza-noche);
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 400;
  line-height: 1.25;
}
.ciba-articulo h3, .articulo h3 {
  color: var(--ciba-crianza-verde);
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 400;
}
.ciba-articulo .cabecera-articulo {
  border-radius: 12px;
  border-bottom: 0;
  background-color: var(--ciba-crianza-noche);
}
.ciba-articulo .navegacion-articulo {
  font-family: Arial, Helvetica, sans-serif;
  border-bottom-color: var(--ciba-crianza-linea);
}
.ciba-articulo .volver, .ciba-articulo .cita,
.ciba-articulo .fuentes a, .tema, .volver {
  color: var(--ciba-crianza-verde);
}
.nota, .respuesta, .alerta, .panel, .interactivo,
.fuentes, .regla, .grupo, .tarjeta, .marco, .podcast,
.video-panel, .infografia {
  max-width: 100%;
  border-radius: 12px;
}
img, video, iframe, svg, canvas {
  max-width: 100%;
}
img, video {
  height: auto;
}
table {
  display: block;
  max-width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
}
button, .boton, .acciones a, .acciones button,
.acciones input[type="button"], .acciones input[type="submit"] {
  min-height: 44px;
}
@media (max-width: 640px) {
  body { font-size: 16px; }
  .ciba-articulo {
    width: calc(100% - 20px);
    margin: 16px auto 36px;
    padding: 20px 18px 30px;
    border-radius: 11px;
  }
  .hero { scroll-margin-top: 76px; }
  .grupo ol { grid-template-columns: 1fr; }
  .reglas, .semaforo { grid-template-columns: 1fr; }
  .acciones { gap: 10px; }
  .acciones a, .acciones button { width: 100%; justify-content: center; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto !important; }
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
}
</style>"""
    cierre = re.search(r"</body\s*>", contenido, flags=re.IGNORECASE)
    if cierre:
        contenido = contenido[:cierre.start()] + estilos + "\n" + contenido[cierre.start():]
    else:
        contenido += "\n" + estilos
    return contenido



def _normalizar_bienestar(contenido: str, archivo_html: Path, raiz_publica: Path) -> str:
    """Estandariza páginas interiores de BIENESTAR con su identidad dorada."""
    try:
        partes = archivo_html.relative_to(raiz_publica).parts
    except ValueError:
        return contenido
    if len(partes) < 3 or partes[0].lower() != "b" or partes[-1].lower() != "index.html":
        return contenido
    if "data-ciba-bienestar-estandar" in contenido:
        return contenido

    estilos = """<style data-ciba-bienestar-estandar>
:root {
  --ciba-bienestar-oro: #8C671F;
  --ciba-bienestar-oscuro: #634916;
  --ciba-bienestar-medio: #B58B3A;
  --ciba-bienestar-acento: #D9B878;
  --ciba-bienestar-marfil: #F7F2E8;
  --ciba-bienestar-papel: #FFFCF5;
  --ciba-bienestar-tinta: #493A32;
  --ciba-bienestar-suave: #75695E;
  --ciba-bienestar-linea: #E5D9C8;
}
body {
  background: var(--ciba-bienestar-marfil) !important;
  color: var(--ciba-bienestar-tinta);
  font-family: Arial, Helvetica, sans-serif;
  font-size: 16px;
  line-height: 1.75;
  -webkit-text-size-adjust: 100%;
}
h1, h2, h3, h4 {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.2;
  text-wrap: balance;
}
a { color: var(--ciba-bienestar-oscuro); text-underline-offset: 3px; }
:where(a,button,input,select,textarea,summary):focus-visible {
  outline: 3px solid var(--ciba-bienestar-medio);
  outline-offset: 3px;
}
.hero {
  color: #fffaf0 !important;
  background:
    radial-gradient(circle at 78% 22%, rgba(217,184,120,.34), transparent 34%),
    linear-gradient(120deg, #634916 0%, #8C671F 58%, #B58B3A 100%) !important;
  border-bottom: 4px solid var(--ciba-bienestar-acento);
}
.hero h1, .hero h2, .hero h3 { color: #fffaf0 !important; }
.hero p, .hero .lead, .hero-descripcion { color: #F7F0E2 !important; }
:where(.eyebrow,.sobrelinea,.kicker) { color: #F0DDBB; }
:where(.wrap,.contenedor) { max-width: 1180px; }
:where(.card,.tile,.tema,.tarjeta,.panel,.recurso,.interactivo,.quiz,.nota,.callout,.figure,.infographic) {
  max-width: 100%;
  border-color: var(--ciba-bienestar-linea);
  border-radius: 12px;
}
:where(.card,.tile,.tema,.tarjeta,.panel,.recurso,.interactivo,.quiz,.figure,.infographic) {
  background: var(--ciba-bienestar-papel);
}
:where(main h2,.seccion h2,.titulo,.grupo-titulo) { color: var(--ciba-bienestar-oscuro); }
:where(main h3,.tema h3,.card h3,.tile h3) { color: var(--ciba-bienestar-oro); }
:where(.nota,.callout,.alerta,.respuesta) { border-left-color: var(--ciba-bienestar-medio); }
:where(.boton,button,.btn,.action,input[type="button"],input[type="submit"]) {
  min-height: 44px;
  border-radius: 8px;
  font: inherit;
}
:where(.boton,.btn,.action,button) {
  background: var(--ciba-bienestar-oscuro);
  color: #fffaf0;
}
:where(input,select,textarea) {
  max-width: 100%;
  min-height: 44px;
  border-color: #C9B58F;
  font: inherit;
}
img,video,iframe,svg,canvas { max-width: 100%; }
img,video { height: auto; }
audio,video,iframe { width: 100%; }
table { max-width: 100%; border-collapse: collapse; }
@media (max-width: 700px) {
  :where(.contenedor,.wrap) { width: min(100% - 28px, 1180px); }
  :where(.grid,.grid2,.lista-temas,.intro-grid,.hero-contenido) {
    grid-template-columns: minmax(0,1fr) !important;
  }
  .hero-contenido { gap: 24px; padding-top: 48px; padding-bottom: 64px; }
  table { display: block; overflow-x: auto; }
  :where(.boton,button,.btn,.action) { min-height: 44px; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto !important; }
  *,*::before,*::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
}
</style>"""
    cierre = re.search(r"</body\s*>", contenido, flags=re.IGNORECASE)
    if cierre:
        contenido = contenido[:cierre.start()] + estilos + "\n" + contenido[cierre.start():]
    else:
        contenido += "\n" + estilos
    return contenido


def _normalizar_acompanamiento(contenido: str, archivo_html: Path, raiz_publica: Path) -> str:
    """Estandariza las páginas interiores de ACOMPAÑAMIENTO con identidad roja."""
    try:
        partes = archivo_html.relative_to(raiz_publica).parts
    except ValueError:
        return contenido
    # La portada de la columna (a/index.html) conserva su diseño de referencia.
    if len(partes) < 3 or partes[0].lower() != "a" or partes[-1].lower() != "index.html":
        return contenido
    if "data-ciba-acompanamiento-estandar" in contenido:
        return contenido

    estilos = """<style data-ciba-acompanamiento-estandar>
:root {
  --ciba-acompanamiento-rojo: #A9443B;
  --ciba-acompanamiento-oscuro: #77352F;
  --ciba-acompanamiento-medio: #C66B5E;
  --ciba-acompanamiento-acento: #D9B878;
  --ciba-acompanamiento-marfil: #F7F2E8;
  --ciba-acompanamiento-papel: #FFFCF5;
  --ciba-acompanamiento-tinta: #493A32;
  --ciba-acompanamiento-suave: #75695E;
  --ciba-acompanamiento-linea: #E5D9C8;
}
body {
  background: var(--ciba-acompanamiento-marfil) !important;
  color: var(--ciba-acompanamiento-tinta);
  font-family: Arial, Helvetica, sans-serif;
  font-size: 16px;
  line-height: 1.75;
  -webkit-text-size-adjust: 100%;
}
h1, h2, h3, h4 {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.2;
  text-wrap: balance;
}
a { color: var(--ciba-acompanamiento-oscuro); text-underline-offset: 3px; }
:where(a,button,input,select,textarea,summary):focus-visible {
  outline: 3px solid var(--ciba-acompanamiento-medio);
  outline-offset: 3px;
}
.hero, .cabecera-articulo {
  color: #fff8eb !important;
  background:
    radial-gradient(circle at 78% 22%, rgba(198,107,94,.32), transparent 34%),
    linear-gradient(120deg, #493A32 0%, #77352F 58%, #A9443B 100%) !important;
  border-bottom: 4px solid var(--ciba-acompanamiento-acento);
}
.hero h1, .hero h2, .hero h3, .cabecera-articulo h1 { color: #fff8eb !important; }
.hero p, .hero .lead, .hero-descripcion { color: #F3E9DE !important; }
:where(.eyebrow,.sobrelinea,.kicker) { color: #EAD8B5; }
:where(.wrap,.contenedor) { max-width: 1180px; }
:where(.card,.tile,.tema,.tarjeta,.panel,.recurso,.interactivo,.quiz,.nota,.callout,.figure,.infographic) {
  max-width: 100%;
  border-color: var(--ciba-acompanamiento-linea);
  border-radius: 12px;
}
:where(.card,.tile,.tema,.tarjeta,.panel,.recurso,.interactivo,.quiz,.figure,.infographic) {
  background: var(--ciba-acompanamiento-papel);
}
:where(main h2,.seccion h2,.titulo,.grupo-titulo,.ciba-articulo h2) {
  color: var(--ciba-acompanamiento-oscuro);
}
:where(main h3,.tema h3,.card h3,.tile h3,.ciba-articulo h3) {
  color: var(--ciba-acompanamiento-rojo);
}
:where(.nota,.callout,.alerta,.respuesta) { border-left-color: var(--ciba-acompanamiento-medio); }
:where(.boton,button,.btn,.action,input[type="button"],input[type="submit"]) {
  min-height: 44px;
  border-radius: 8px;
  font: inherit;
}
:where(.boton,.btn,.action,button) {
  background: var(--ciba-acompanamiento-oscuro);
  color: #fff8eb;
}
:where(input,select,textarea) {
  max-width: 100%;
  min-height: 44px;
  border-color: #C9B5A8;
  font: inherit;
}
img,video,iframe,svg,canvas { max-width: 100%; }
img,video { height: auto; }
audio,video,iframe { max-width: 100%; }
table { max-width: 100%; border-collapse: collapse; }
@media (max-width: 700px) {
  :where(.contenedor,.wrap) { width: min(100% - 28px, 1180px); }
  :where(.grid,.grid2,.lista-temas,.intro-grid,.hero-contenido) {
    grid-template-columns: minmax(0,1fr) !important;
  }
  .hero-contenido { gap: 24px; padding-top: 48px; padding-bottom: 64px; }
  table { display: block; overflow-x: auto; }
  :where(.boton,button,.btn,.action) { min-height: 44px; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto !important; }
  *,*::before,*::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
}
</style>"""
    cierre = re.search(r"</body\s*>", contenido, flags=re.IGNORECASE)
    if cierre:
        contenido = contenido[:cierre.start()] + estilos + "\n" + contenido[cierre.start():]
    else:
        contenido += "\n" + estilos
    return contenido

def _conectar_sistema_global(
    archivo_html: Path,
    raiz_publica: Path,
    catalogo: dict | None = None,
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
    contenido = _normalizar_migas_y_metadatos(contenido, archivo_html, raiz_publica, catalogo)
    contenido = _normalizar_estilo_informatica(contenido, archivo_html, raiz_publica)
    contenido = _normalizar_sistema_editorial(contenido, archivo_html, raiz_publica)
    contenido = _normalizar_crianza(contenido, archivo_html, raiz_publica)
    contenido = _normalizar_bienestar(contenido, archivo_html, raiz_publica)
    contenido = _normalizar_acompanamiento(contenido, archivo_html, raiz_publica)

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
            r'\1?v=20261119-01\2',
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




def _paleta_columna(letra: str) -> dict[str, str]:
    """Identidad visual estable para cada columna editorial."""
    return {
        "c": {"nombre": "CRIANZA", "oscuro": "#172b27", "medio": "#526e56", "acento": "#d9b878", "fondo": "#f5f0e5", "papel": "#fffdf7", "tinta": "#29332d"},
        "i": {"nombre": "INFORMÁTICA", "oscuro": "#12364d", "medio": "#174f70", "acento": "#d5b879", "fondo": "#f5f3ec", "papel": "#fffefa", "tinta": "#273943"},
        "b": {"nombre": "BIENESTAR", "oscuro": "#493a32", "medio": "#8c671f", "acento": "#d9b878", "fondo": "#f7f2e8", "papel": "#fffcf5", "tinta": "#493a32"},
        "a": {"nombre": "ACOMPAÑAMIENTO", "oscuro": "#493a32", "medio": "#a9443b", "acento": "#e3b28b", "fondo": "#f7f2e8", "papel": "#fffcf5", "tinta": "#493a32"},
    }.get(letra.lower(), {"nombre": "CIBA", "oscuro": "#172b27", "medio": "#526e56", "acento": "#d9b878", "fondo": "#f5f0e5", "papel": "#fffdf7", "tinta": "#29332d"})




def _generar_indice_area(
    tmp: Path,
    letra: str,
    datos: dict,
) -> list[ValidationError]:
    """Genera una página de área coherente cuando existe metadata pero falta index.html."""
    errores: list[ValidationError] = []
    id_area = str(datos.get("id", ""))
    destino = tmp / letra.lower() / id_area
    destino.mkdir(parents=True, exist_ok=True)
    paleta = _paleta_columna(letra)
    titulo = html_escape(str(datos.get("titulo", id_area)))
    descripcion = html_escape(str(datos.get("descripcion", "")), quote=True)
    columna_href = os.path.relpath(tmp / letra.lower() / "index.html", destino).replace(os.sep, "/")
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="{paleta['oscuro']}"><meta name="description" content="{descripcion}">
<title>{titulo} | {paleta['nombre']} · CIBA</title>
<style>
:root{{--oscuro:{paleta['oscuro']};--medio:{paleta['medio']};--acento:{paleta['acento']};--fondo:{paleta['fondo']};--papel:{paleta['papel']};--tinta:{paleta['tinta']}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fondo);color:var(--tinta);font-family:Arial,Helvetica,sans-serif}}
.wrap{{width:min(1040px,calc(100% - 36px));margin:auto}}
.hero{{padding:clamp(48px,8vw,82px) 0 58px;color:#fff;background:linear-gradient(120deg,var(--oscuro),var(--medio));border-bottom:4px solid var(--acento)}}
.kicker{{color:var(--acento);font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase}}
h1{{max-width:850px;margin:20px 0 14px;font:400 clamp(36px,6vw,62px)/1.08 Georgia,serif}}
.intro{{max-width:760px;color:#ffffffdf;font-size:15px;line-height:1.85}}
main{{padding:42px 0 72px}}.nota{{padding:28px;border-left:3px solid var(--acento);background:var(--papel);line-height:1.8;box-shadow:0 10px 28px #00000008}}
.nota h2{{margin:0 0 10px;color:var(--oscuro);font:400 26px Georgia,serif}}
.nota p{{margin:0;color:#68736e;font-size:14px}}
footer{{padding:24px 0;background:var(--oscuro);color:#ffffffd6;font-size:11px}}footer a{{color:var(--acento);text-decoration:none}}
</style></head><body>
<header class="hero"><div class="wrap"><div class="kicker">ÁREA TEMÁTICA · {html_escape(id_area)}</div><h1>{titulo}</h1><p class="intro">{descripcion}</p></div></header>
<main class="wrap"><section class="nota"><h2>Este espacio forma parte de CIBA</h2><p>La estructura temática ya está disponible. Los artículos y recursos propios de esta área se incorporarán cuando estén preparados y aprobados para su difusión.</p></section></main>
<footer><div class="wrap">CIBA · Crecemos acompañándonos · <a href="{html_escape(columna_href, quote=True)}">Volver a {paleta['nombre']}</a></div></footer>
</body></html>"""
    try:
        (destino / "index.html").write_text(html, encoding="utf-8")
    except OSError as exc:
        errores.append(ValidationError(f"{letra}/{id_area}", "índice de área", f"no se pudo generar: {exc}"))
    return errores


def _generar_indice_subseccion(
    src: Path,
    tmp: Path,
    letra: str,
    area_dir: Path,
    subseccion_dir: Path,
    datos: dict,
) -> tuple[list[ValidationError], int]:
    """Crea una página propia para cada subsección archivada que agrupa artículos."""
    errores: list[ValidationError] = []
    rel = str(subseccion_dir.relative_to(src))
    hijos, errs_hijos = listar_directorios_seguros(subseccion_dir, rel)
    errores.extend(errs_hijos)
    destino = tmp / letra.lower() / area_dir.name / subseccion_dir.relative_to(area_dir)
    destino.mkdir(parents=True, exist_ok=True)
    paleta = _paleta_columna(letra)
    area_meta = _leer_json(area_dir / "area.json")
    titulo = html_escape(str(datos.get("titulo", subseccion_dir.name)))
    descripcion = html_escape(str(datos.get("descripcion", "")))
    id_sub = html_escape(str(datos.get("id", subseccion_dir.name)))
    titulo_area = html_escape(str(area_meta.get("titulo", area_dir.name)))
    tarjetas: list[str] = []
    articulos_publicados = 0

    for hijo in hijos:
        if hijo.name == "_paginas":
            continue
        meta_path = hijo / "meta.json"
        if not meta_path.is_file() or meta_path.is_symlink():
            continue
        try:
            hijo_meta = _leer_json(meta_path)
        except (OSError, json.JSONDecodeError):
            continue
        estado = hijo_meta.get("estado")
        if estado not in ("publicado", "archivado"):
            continue
        ruta_destino = tmp / letra.lower() / area_dir.name / hijo.relative_to(area_dir)
        href = os.path.relpath(ruta_destino, destino).replace(os.sep, "/").rstrip("/") + "/"
        tipo = "Subsección" if estado == "archivado" else "Artículo"
        if estado == "publicado":
            articulos_publicados += 1
        tarjetas.append(
            '<a class="item" href="' + html_escape(href, quote=True) + '">'
            '<span class="tipo">' + tipo + ' · ' + html_escape(str(hijo_meta.get("id", ""))) + '</span>'
            '<h2>' + html_escape(str(hijo_meta.get("titulo", hijo.name))) + '</h2>'
            '<p>' + html_escape(str(hijo_meta.get("descripcion", ""))) + '</p>'
            '<span class="ir">Abrir contenido →</span></a>'
        )

    if not tarjetas:
        tarjetas.append(
            '<div class="vacio"><strong>Esta subsección está organizada.</strong>'
            '<p>Los artículos se incorporarán aquí cuando estén aprobados para su difusión.</p></div>'
        )

    area_href = os.path.relpath(tmp / letra.lower() / area_dir.name, destino).replace(os.sep, "/").rstrip("/") + "/"
    columna_href = os.path.relpath(tmp / letra.lower(), destino).replace(os.sep, "/").rstrip("/") + "/"
    home_href = os.path.relpath(tmp, destino).replace(os.sep, "/").rstrip("/") + "/"
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="{paleta['oscuro']}">
<meta name="description" content="{descripcion}">
<title>{titulo} | {paleta['nombre']} · CIBA</title>
<style>
:root{{--oscuro:{paleta['oscuro']};--medio:{paleta['medio']};--acento:{paleta['acento']};--fondo:{paleta['fondo']};--papel:{paleta['papel']};--tinta:{paleta['tinta']}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fondo);color:var(--tinta);font-family:Arial,Helvetica,sans-serif}}
.wrap{{width:min(1040px,calc(100% - 36px));margin:auto}}
.hero{{padding:clamp(48px,8vw,82px) 0 58px;color:#fff;background:linear-gradient(120deg,var(--oscuro),var(--medio));border-bottom:4px solid var(--acento)}}
.breadcrumb{{display:flex;flex-wrap:wrap;gap:9px;color:#ffffffc9;font-size:11px}}.breadcrumb a{{color:#fff;text-decoration:none}}
.kicker{{margin:34px 0 12px;color:var(--acento);font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase}}
h1{{max-width:850px;margin:0;font:400 clamp(36px,6vw,62px)/1.08 Georgia,serif}}
.intro{{max-width:760px;margin:18px 0 0;color:#ffffffdf;font-size:15px;line-height:1.85}}
main{{padding:38px 0 70px}}.resumen{{margin:0 0 25px;padding:17px 20px;border-left:3px solid var(--acento);background:var(--papel);font-size:13px;line-height:1.7}}
.lista{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));gap:16px}}
.item{{display:flex;flex-direction:column;min-height:220px;padding:24px;border:1px solid #00000012;border-radius:12px;background:var(--papel);color:inherit;text-decoration:none;box-shadow:0 8px 24px #00000008;transition:transform .18s,box-shadow .18s}}
.item:hover{{transform:translateY(-3px);box-shadow:0 14px 30px #00000012}}
.tipo{{color:var(--medio);font-size:10px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}}
.item h2{{margin:13px 0 9px;font:400 24px/1.2 Georgia,serif;color:var(--oscuro)}}
.item p{{margin:0 0 18px;color:#68736e;font-size:13px;line-height:1.75}}
.ir{{margin-top:auto;color:var(--medio);font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}
.vacio{{grid-column:1/-1;padding:25px;background:var(--papel);border:1px solid #00000012;border-radius:12px;line-height:1.7}}
.vacio p{{margin-bottom:0;color:#68736e;font-size:13px}}
footer{{padding:24px 0;background:var(--oscuro);color:#ffffffd6;font-size:11px}}
footer a{{color:var(--acento);text-decoration:none}}
@media(max-width:600px){{.hero{{padding:48px 0 42px}}.item{{min-height:0;padding:20px}}}}
</style>
</head>
<body>
<header class="hero"><div class="wrap">
<nav class="breadcrumb"><a href="{home_href}">CIBA</a><span>›</span><a href="{columna_href}">{paleta['nombre']}</a><span>›</span><a href="{area_href}">{titulo_area}</a></nav>
<div class="kicker">SUBSECCIÓN · {id_sub}</div><h1>{titulo}</h1><p class="intro">{descripcion}</p>
</div></header>
<main class="wrap"><div class="resumen"><strong>Explora esta subsección.</strong> Aquí encontrarás sus artículos y recursos relacionados, organizados en páginas independientes.</div>
<div class="lista">{''.join(tarjetas)}</div></main>
<footer><div class="wrap">CIBA · Crecemos acompañándonos · <a href="{area_href}">Volver a {titulo_area}</a></div></footer>
</body></html>"""
    try:
        (destino / "index.html").write_text(html, encoding="utf-8")
    except OSError as exc:
        errores.append(ValidationError(rel, "índice de subsección", f"no se pudo generar: {exc}"))
    return errores, articulos_publicados


def _generar_portadas_columnas_ausentes(
    tmp: Path,
    areas: list[dict],
    columnas: list[dict],
) -> list[ValidationError]:
    """Completa portadas de columna ausentes sin alterar las portadas existentes."""
    errores: list[ValidationError] = []
    for columna in columnas:
        letra = str(columna.get("id", "")).lower()
        if letra not in ("c", "i", "b", "a"):
            continue
        destino = tmp / letra / "index.html"
        if destino.is_file():
            continue
        propias = [a for a in areas if str(a.get("columna", "")).lower() == letra]
        if not propias:
            continue
        paleta = _paleta_columna(letra)
        tarjetas = []
        for area in sorted(propias, key=lambda a: (a.get("orden", 0), a.get("id", ""))):
            ruta = str(area.get("ruta_publica", ""))
            ruta_destino = tmp / ruta
            href = os.path.relpath(ruta_destino, tmp / letra).replace(os.sep, "/").rstrip("/") + "/"
            titulo = html_escape(str(area.get("titulo", area.get("id", "Área"))))
            descripcion = html_escape(str(area.get("descripcion", "")))
            tarjetas.append(
                '<a class="item" href="' + html_escape(href, quote=True) + '">'
                '<span>' + html_escape(str(area.get("id", ""))) + '</span>'
                '<h2>' + titulo + '</h2><p>' + descripcion + '</p><b>Explorar área →</b></a>'
            )
        nombre = html_escape(str(columna.get("titulo", paleta["nombre"])))
        descripcion_col = html_escape(str(columna.get("descripcion", "")))
        html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="{paleta['oscuro']}"><meta name="description" content="{descripcion_col}">
<title>{nombre} | CIBA · Crecemos acompañándonos</title>
<style>
:root{{--oscuro:{paleta['oscuro']};--medio:{paleta['medio']};--acento:{paleta['acento']};--fondo:{paleta['fondo']};--papel:{paleta['papel']};--tinta:{paleta['tinta']}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fondo);color:var(--tinta);font-family:Arial,Helvetica,sans-serif}}
.wrap{{width:min(1120px,calc(100% - 40px));margin:auto}}.hero{{padding:76px 0 65px;color:white;background:linear-gradient(120deg,var(--oscuro),var(--medio));border-bottom:4px solid var(--acento)}}
.kicker{{color:var(--acento);font-size:10px;font-weight:800;letter-spacing:.2em}}h1{{margin:20px 0 14px;font:400 clamp(42px,7vw,72px)/1.05 Georgia,serif}}.hero p{{max-width:720px;color:#ffffffdf;line-height:1.85;font-size:15px}}
main{{padding:48px 0 75px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:17px}}
.item{{display:block;padding:25px;border:1px solid #00000012;border-radius:12px;background:var(--papel);color:inherit;text-decoration:none;box-shadow:0 8px 25px #00000008}}
.item span{{color:var(--medio);font-size:10px;font-weight:800;letter-spacing:.15em}}.item h2{{margin:12px 0 8px;color:var(--oscuro);font:400 25px Georgia,serif}}.item p{{color:#68736e;font-size:13px;line-height:1.75}}.item b{{color:var(--medio);font-size:10px;letter-spacing:.1em;text-transform:uppercase}}
footer{{padding:24px 0;background:var(--oscuro);color:#ffffffd6;font-size:11px}}
</style></head><body><header class="hero"><div class="wrap"><div class="kicker">CIBA · COLUMNA EDITORIAL</div><h1>{nombre}</h1><p>{descripcion_col}</p></div></header>
<main class="wrap"><div class="grid">{''.join(tarjetas)}</div></main><footer><div class="wrap">CIBA · Crecemos acompañándonos</div></footer></body></html>"""
        destino.parent.mkdir(parents=True, exist_ok=True)
        try:
            destino.write_text(html, encoding="utf-8")
        except OSError as exc:
            errores.append(ValidationError(f"{letra}/index.html", "portada de columna", f"no se pudo generar: {exc}"))
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
    subsecciones_publicadas: list[dict] = []

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
        else:
            errores.extend(_generar_indice_area(tmp, letra.lower(), area_meta.datos))

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

            estado_pagina = pagina.datos.get("estado")
            es_preview = (
                estado_pagina == "revision"
                and pagina.datos.get("preview_publica") is True
            )

            if estado_pagina == "archivado":
                ruta_relativa = pag_dir.relative_to(area_dir).as_posix()
                ruta_publica = f"{letra.lower()}/{area_dir.name}/{ruta_relativa}/"
                errs_sub, total_articulos = _generar_indice_subseccion(
                    src, tmp, letra.lower(), area_dir, pag_dir, pagina.datos
                )
                errores.extend(errs_sub)
                subsecciones_publicadas.append({
                    "id": pagina.datos.get("id", pag_dir.name),
                    "titulo": pagina.datos.get("titulo", pag_dir.name),
                    "descripcion": pagina.datos.get("descripcion", ""),
                    "columna": letra,
                    "area": area_meta.datos.get("id", area_dir.name),
                    "ruta_publica": ruta_publica,
                    "articulos_publicados_directos": total_articulos,
                })
                continue

            if estado_pagina != "publicado" and not es_preview:
                continue

            ruta_relativa = pag_dir.relative_to(area_dir).as_posix()
            ruta_publica = (
                f"{letra.lower()}/{area_dir.name}/{ruta_relativa}/"
            )
            destino_pagina = tmp / ruta_publica

            errs_copia = _copiar_pagina_publica(
                pag_dir,
                destino_pagina,
                pagina.fotos_validadas,
                rel_pag,
            )
            errores.extend(errs_copia)

            # Las vistas previas son accesibles por URL, pero no se incorporan
            # al catálogo ni se presentan como artículos publicados.
            if es_preview:
                continue

            registro = {
                **pagina.datos,
                "ruta_publica": ruta_publica,
            }
            paginas_publicadas.append(registro)

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
        "subsecciones": sorted(
            subsecciones_publicadas,
            key=lambda s: (s.get("columna", ""), s.get("area", ""), s.get("id", "")),
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

    # Portadas editoriales de las columnas en sus rutas raíz.
    errores.extend(_copiar_indices_columnas(src, tmp))
    errores.extend(_generar_portadas_columnas_ausentes(tmp, areas_registradas, columnas_cfg.columnas))

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
        catalogo_global = _leer_json(tmp / "data" / "catalogo.json")

        for archivo_html in paginas_html:
            errs_global = _conectar_sistema_global(
                archivo_html,
                tmp,
                catalogo_global,
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
                    r'\1?v=20261119-01\2',
                    html,
                    flags=re.IGNORECASE,
                )
                html_actualizado = re.sub(
                    r'(<script\b[^>]*\bsrc\s*=\s*["\'][^"\']*ciba-plataforma\.js)(?:[?#][^"\']*)?(["\'][^>]*>)',
                    r'\1?v=20261119-01\2',
                    html_actualizado,
                    flags=re.IGNORECASE,
                )
                html_actualizado = re.sub(
                    r'(import\s*\(\s*["\'][^"\']*ciba-plataforma\.js)(?:[?#][^"\']*)?(["\']\s*\))',
                    r'\1?v=20261119-01\2',
                    html_actualizado,
                    flags=re.IGNORECASE,
                )
                html_actualizado = re.sub(
                    r'(root\s*\+\s*["\'][^"\']*ciba-plataforma\.js)(?:[?#][^"\']*)?(["\'])',
                    r'\1?v=20261119-01\2',
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

        # Auditoría de cobertura: ninguna página pública debe quedar fuera
        # del sistema global ni cargar una versión antigua en caché.
        try:
            codigo_global = script_global.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errores.append(
                ValidationError(
                    "assets/js/ciba-global.js",
                    "cobertura de movimiento",
                    f"no se pudo comprobar el módulo global: {exc}",
                )
            )
            codigo_global = ""

        if "ciba-global.css?v=20261112-08" not in codigo_global:
            errores.append(
                ValidationError(
                    "assets/js/ciba-global.js",
                    "cobertura de movimiento",
                    "la hoja global no utiliza la versión institucional vigente",
                )
            )

        for archivo_html in sorted(tmp.rglob("*.html")):
            try:
                html = archivo_html.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                errores.append(
                    ValidationError(
                        str(archivo_html.relative_to(tmp)),
                        "cobertura de movimiento",
                        f"no se pudo leer la página publicada: {exc}",
                    )
                )
                continue

            referencias_globales = re.findall(
                r'<script\b(?=[^>]*\bsrc\s*=\s*["\'][^"\']*ciba-global\.js(?:[?#][^"\']*)?["\'])[^>]*>',
                html,
                flags=re.IGNORECASE,
            )

            version_correcta = (
                len(referencias_globales) == 1
                and re.search(
                    r"""ciba-global\.js\?v=20261119-01(?:["']|\s)""",
                    referencias_globales[0],
                    flags=re.IGNORECASE,
                )
            )

            if not version_correcta:
                errores.append(
                    ValidationError(
                        str(archivo_html.relative_to(tmp)),
                        "cobertura de movimiento",
                        "la página debe cargar una sola vez el sistema global en su versión vigente",
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