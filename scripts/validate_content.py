"""Validador real de contenidos CIBA.

Uso:
    python scripts/validate_content.py --src content
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from lib.area_reader import leer_area
from lib.columnas_reader import leer_columnas
from lib.errors import ValidationError
from lib.meta_reader import leer_meta
from lib.paths import COLUMNAS_CARPETAS_OFICIALES, COLUMNAS_VALIDAS
from lib.safety import es_ruta_segura, listar_directorios_seguros, validar_raiz


def _verificar_columnas_fisicas(src: Path) -> list[ValidationError]:
    """Comprueba exactamente content/c, content/i, content/b, content/a.

    - Detecta columnas ausentes.
    - Detecta duplicados por mayúsculas (p. ej. c y C).
    - Detecta carpetas de columna con nombre inválido.
    """
    errores: list[ValidationError] = []
    if not src.is_dir():
        errores.append(ValidationError("content", "carpeta", "no existe"))
        return errores
    if src.is_symlink():
        errores.append(ValidationError("content", "carpeta", "es symlink"))
        return errores

    try:
        entradas = list(src.iterdir())
    except OSError as exc:
        errores.append(ValidationError("content", "carpeta", f"no legible: {exc}"))
        return errores

    presentes: dict[str, list[str]] = {c: [] for c in COLUMNAS_CARPETAS_OFICIALES}

    for entrada in entradas:
        if entrada.is_symlink():
            errores.append(ValidationError(f"content/{entrada.name}", "symlink", "symlink en columna"))
            continue
        if not entrada.is_dir():
            continue
        nombre = entrada.name
        minu = nombre.lower()
        if minu in COLUMNAS_CARPETAS_OFICIALES:
            presentes[minu].append(nombre)
        elif nombre == "_esquema":
            continue
        else:
            errores.append(ValidationError(f"content/{nombre}", "carpeta", "nombre de columna inválido"))

    for oficial in COLUMNAS_CARPETAS_OFICIALES:
        nombres = presentes[oficial]
        if not nombres:
            errores.append(ValidationError(f"content/{oficial}", "carpeta", "columna ausente"))
        elif len(nombres) > 1:
            errores.append(ValidationError(f"content/{oficial}", "carpeta", f"duplicado por mayúsculas: {nombres}"))
        elif nombres[0] != oficial:
            errores.append(ValidationError(f"content/{nombres[0]}", "carpeta", f"debe llamarse '{oficial}'"))

    return errores


def validar(src: Path, *, hoy: date | None = None) -> list[ValidationError]:
    errores: list[ValidationError] = []

    errs_cols_fis = _verificar_columnas_fisicas(src)
    errores.extend(errs_cols_fis)

    esquema = src / "_esquema"
    if not esquema.is_dir():
        errores.append(ValidationError("content/_esquema", "carpeta", "no existe"))
        return errores
    if esquema.is_symlink():
        errores.append(ValidationError("content/_esquema", "carpeta", "es symlink"))
        return errores

    columnas, errs_cols = leer_columnas(esquema / "columnas.json", "content/_esquema/columnas.json")
    errores.extend(errs_cols)
    if columnas is None:
        return errores

    for req in ("meta.schema.json", "area.schema.json"):
        r = esquema / req
        if not r.is_file() or r.is_symlink():
            errores.append(ValidationError(f"content/_esquema/{req}", "archivo", "ausente o symlink"))

    ids_paginas: dict[str, str] = {}
    ids_areas: dict[str, str] = {}

    for letra in COLUMNAS_CARPETAS_OFICIALES:
        carpeta_col = src / letra
        if not carpeta_col.is_dir() or carpeta_col.is_symlink():
            continue  # ya reportado arriba

        subdirs, errs_sub = listar_directorios_seguros(carpeta_col, f"content/{letra}")
        errores.extend(errs_sub)

        for carpeta_area in subdirs:
            rel_area = str(carpeta_area.relative_to(src))
            ok, motivo = es_ruta_segura(src, carpeta_area)
            if not ok:
                errores.append(ValidationError(rel_area, "ruta", motivo))
                continue

            area_meta, errs_area = leer_area(carpeta_area / "area.json", rel_area)
            errores.extend(errs_area)
            if area_meta is None:
                continue

            id_area = area_meta.datos.get("id")
            if isinstance(id_area, str):
                if id_area in ids_areas:
                    errores.append(ValidationError(rel_area, "id", f"duplicado ({ids_areas[id_area]})"))
                else:
                    ids_areas[id_area] = rel_area
                if not id_area.startswith(letra.upper()):
                    errores.append(ValidationError(rel_area, "id", f"debe empezar por {letra.upper()}"))
                if id_area != carpeta_area.name:
                    errores.append(ValidationError(rel_area, "id", f"{id_area!r} ≠ carpeta {carpeta_area.name!r}"))

            col_area = area_meta.datos.get("columna")
            if isinstance(col_area, str) and col_area != letra.upper():
                errores.append(ValidationError(rel_area, "columna", f"{col_area!r} ≠ {letra.upper()!r}"))

            pendientes = list(reversed(listar_directorios_seguros(carpeta_area, rel_area)[0]))
            _, errs_pag_dir = listar_directorios_seguros(carpeta_area, rel_area)
            errores.extend(errs_pag_dir)

            while pendientes:
                carpeta_pag = pendientes.pop()
                if carpeta_pag.name == "_paginas":
                    ok_aux, motivo_aux = es_ruta_segura(src, carpeta_pag)
                    if not ok_aux:
                        errores.append(ValidationError(str(carpeta_pag.relative_to(src)), "ruta", motivo_aux))
                    continue

                rel_pag = str(carpeta_pag.relative_to(src))
                ok, motivo = es_ruta_segura(src, carpeta_pag)
                if not ok:
                    errores.append(ValidationError(rel_pag, "ruta", motivo))
                    continue

                pagina, errs_pag = leer_meta(carpeta_pag / "meta.json", rel_pag, hoy=hoy)
                errores.extend(errs_pag)
                if pagina is None:
                    continue

                id_pag = pagina.datos.get("id")
                if isinstance(id_pag, str):
                    if id_pag in ids_paginas:
                        errores.append(ValidationError(rel_pag, "id", f"duplicado ({ids_paginas[id_pag]})"))
                    else:
                        ids_paginas[id_pag] = rel_pag
                    if isinstance(id_area, str) and not id_pag.startswith(id_area + "-"):
                        errores.append(ValidationError(rel_pag, "id", f"debe empezar por {id_area}-"))

                col_pag = pagina.datos.get("columna")
                if isinstance(col_pag, str) and col_pag != letra.upper():
                    errores.append(ValidationError(rel_pag, "columna", f"{col_pag!r} ≠ {letra.upper()!r}"))

                area_pag = pagina.datos.get("area")
                if isinstance(area_pag, str) and isinstance(id_area, str) and area_pag != id_area:
                    errores.append(ValidationError(rel_pag, "area", f"{area_pag!r} ≠ área {id_area!r}"))

                if pagina.datos.get("estado") == "publicado":
                    index = carpeta_pag / "index.html"
                    ok_idx, motivo_idx = es_ruta_segura(carpeta_pag, index)
                    if not ok_idx:
                        errores.append(ValidationError(rel_pag, "index.html", motivo_idx))
                    elif not index.is_file() or index.stat().st_size < 200:
                        errores.append(ValidationError(rel_pag, "index.html", "publicado sin contenido suficiente"))

                # Los contenedores archivados representan subsecciones, no artículos.
                # Se inspeccionan sus hijos para encontrar páginas anidadas.
                if pagina.datos.get("estado") == "archivado":
                    hijos, errs_hijos = listar_directorios_seguros(carpeta_pag, rel_pag)
                    errores.extend(errs_hijos)
                    pendientes.extend(reversed(hijos))

    return errores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida contenidos CIBA.")
    parser.add_argument("--src", default="content", type=Path)
    args = parser.parse_args(argv)

    errores = validar(args.src)
    if errores:
        for e in errores:
            print(e, file=sys.stderr)
        print(f"\n{len(errores)} error(es).", file=sys.stderr)
        return 1
    print(f"OK: {args.src} válido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
