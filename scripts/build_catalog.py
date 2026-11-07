"""Generador del catálogo CIBA con build atómico, allowlist y anti-symlink.

Uso:
    python scripts/build_catalog.py --src content --out dist
"""

from __future__ import annotations

import argparse
import json
import os
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
        yield pag_dir


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
        errores.append(ValidationError(rel_pagina, "index.html", f"copia falló: {exc}"))
        return errores

    if fotos_validadas:
        errs_media = copiar_media_autorizada(origen_pagina, destino_pagina, fotos_validadas, rel_pagina)
        errores.extend(errs_media)

    permitidos = set(PERMITIDOS_EN_PAGINA) | {f.ruta_relativa for f in fotos_validadas}
    errs_clean = verificar_destino_sin_extranos(destino_pagina, permitidos, rel_pagina)
    errores.extend(errs_clean)
    return errores


def _construir_en_tmp(src: Path, tmp: Path, hoy: date | None) -> list[ValidationError]:
    errores: list[ValidationError] = []
    esquema = src / "_esquema"
    columnas_cfg, errs_cols = leer_columnas(esquema / "columnas.json", "content/_esquema/columnas.json")
    errores.extend(errs_cols)
    if columnas_cfg is None:
        return errores

    areas_registradas: list[dict] = []
    paginas_publicadas: list[dict] = []

    for letra, area_dir in _iter_areas(src):
        rel_area = str(area_dir.relative_to(src))
        area_meta, errs_area = leer_area(area_dir / "area.json", rel_area)
        errores.extend(errs_area)
        if area_meta is None:
            continue

        areas_registradas.append(
            {**area_meta.datos, "ruta_publica": f"{letra.lower()}/{area_dir.name}/"}
        )

        for pag_dir in _iter_paginas(area_dir):
            rel_pag = str(pag_dir.relative_to(src))
            pagina, errs_pag = leer_meta(pag_dir / "meta.json", rel_pag, hoy=hoy)
            errores.extend(errs_pag)
            if pagina is None:
                continue
            if pagina.datos.get("estado") != "publicado":
                continue

            registro = {
                **pagina.datos,
                "ruta_publica": f"{letra.lower()}/{area_dir.name}/{pag_dir.name}/",
            }
            paginas_publicadas.append(registro)

            destino_pagina = tmp / registro["ruta_publica"]
            errs_copia = _copiar_pagina_publica(
                pag_dir, destino_pagina, pagina.fotos_validadas, rel_pag
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
            key=lambda a: (a.get("columna", ""), a.get("orden", 0), a.get("id", "")),
        ),
        "paginas": sorted(
            paginas_publicadas,
            key=lambda p: (p.get("columna", ""), p.get("area", ""), p.get("id", "")),
        ),
    }

    (tmp / "data" / "catalogo.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (tmp / "data" / "columnas.json").write_text(
        json.dumps(columnas_cfg.datos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (tmp / "data" / "areas.json").write_text(
        json.dumps({"version": 1, "areas": catalogo["areas"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # La portada del sitio también forma parte del artefacto público.
    portada = src.parent / "index.html"
    if portada.exists() or portada.is_symlink():
        ok, motivo = es_ruta_segura(src.parent, portada)
        if not ok:
            errores.append(ValidationError("index.html", "portada", motivo))
        elif not portada.is_file():
            errores.append(ValidationError("index.html", "portada", "no es archivo"))
        else:
            try:
                shutil.copy2(portada, tmp / "index.html")
            except OSError as exc:
                errores.append(ValidationError("index.html", "portada", f"copia fallida: {exc}"))

    errs_assets = _copiar_assets(src.parent, tmp)
    errores.extend(errs_assets)
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
                errores.append(f"CRÍTICO: no se pudo restaurar dist/: {exc2}")
        return errores

    if not (out / "data" / "catalogo.json").is_file():
        errores.append("instalación verificada fallida: catalogo.json no presente")
        if tenia_anterior and backup.exists():
            shutil.rmtree(out, ignore_errors=True)
            try:
                os.replace(backup, out)
                errores.append("dist/ anterior restaurado desde backup")
            except OSError as exc3:
                errores.append(f"CRÍTICO: no se pudo restaurar dist/: {exc3}")
        return errores

    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    return errores


def construir(src: Path, out: Path, *, hoy: date | None = None) -> int:
    errores = validar(src, hoy=hoy)
    if errores:
        for e in errores:
            print(e, file=sys.stderr)
        print(f"\n{len(errores)} error(es). No se genera catálogo; dist/ anterior intacto.", file=sys.stderr)
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
        f"({len(_leer_json(out / 'data' / 'catalogo.json')['paginas'])} páginas publicadas)."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera el catálogo CIBA.")
    parser.add_argument("--src", default="content", type=Path)
    parser.add_argument("--out", default="dist", type=Path)
    args = parser.parse_args(argv)
    return construir(args.src, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
