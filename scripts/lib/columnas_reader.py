"""Validación estricta de content/_esquema/columnas.json (raíz e hijos)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .paths import COLUMNAS_VALIDAS

CAMPOS_RAIZ = ("version", "columnas")
CAMPOS_COLUMNA = ("id", "titulo", "descripcion", "orden", "icono")


@dataclass
class ColumnasConfig:
    ruta: Path
    datos: dict[str, Any] = field(default_factory=dict)
    columnas: list[dict] = field(default_factory=list)


def leer_columnas(ruta: Path, ruta_relativa: str) -> tuple[ColumnasConfig | None, list[ValidationError]]:
    errores: list[ValidationError] = []
    if not ruta.is_file():
        errores.append(ValidationError(ruta_relativa, "archivo", "ausente"))
        return None, errores
    if ruta.is_symlink():
        errores.append(ValidationError(ruta_relativa, "archivo", "es symlink"))
        return None, errores

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errores.append(ValidationError(ruta_relativa, "json", f"inválido: {exc}"))
        return None, errores

    if not isinstance(datos, dict):
        errores.append(ValidationError(ruta_relativa, "raíz", "debe ser objeto JSON"))
        return None, errores

    # Raíz: solo version y columnas
    extra_raiz = set(datos.keys()) - set(CAMPOS_RAIZ)
    if extra_raiz:
        errores.append(ValidationError(ruta_relativa, "raíz", f"campos desconocidos: {sorted(extra_raiz)}"))

    if "version" not in datos:
        errores.append(ValidationError(ruta_relativa, "version", "ausente"))
    else:
        v = datos["version"]
        if v is None:
            errores.append(ValidationError(ruta_relativa, "version", "no puede ser null"))
        elif isinstance(v, bool) or not isinstance(v, int):
            errores.append(ValidationError(ruta_relativa, "version", "entero estricto (no bool)"))

    if "columnas" not in datos:
        errores.append(ValidationError(ruta_relativa, "columnas", "ausente"))
        return ColumnasConfig(ruta=ruta, datos=datos, columnas=[]), errores

    lista = datos["columnas"]
    if lista is None:
        errores.append(ValidationError(ruta_relativa, "columnas", "no puede ser null"))
        return ColumnasConfig(ruta=ruta, datos=datos, columnas=[]), errores
    if not isinstance(lista, list):
        errores.append(ValidationError(ruta_relativa, "columnas", "debe ser lista"))
        return ColumnasConfig(ruta=ruta, datos=datos, columnas=[]), errores

    if len(lista) != 4:
        errores.append(ValidationError(ruta_relativa, "columnas", f"exactamente 4 columnas, hay {len(lista)}"))

    ids_vistos: list[str] = []
    for i, col in enumerate(lista):
        prefijo = f"columnas[{i}]"
        if not isinstance(col, dict):
            errores.append(ValidationError(ruta_relativa, prefijo, "objeto"))
            continue
        extra = set(col.keys()) - set(CAMPOS_COLUMNA)
        if extra:
            errores.append(ValidationError(ruta_relativa, prefijo, f"campos desconocidos: {sorted(extra)}"))
        for campo in CAMPOS_COLUMNA:
            if campo not in col:
                errores.append(ValidationError(ruta_relativa, f"{prefijo}.{campo}", "ausente"))
            elif col[campo] is None:
                errores.append(ValidationError(ruta_relativa, f"{prefijo}.{campo}", "no puede ser null"))

        id_col = col.get("id")
        if isinstance(id_col, str):
            if id_col not in COLUMNAS_VALIDAS:
                errores.append(ValidationError(ruta_relativa, f"{prefijo}.id", f"inválido: {id_col!r}"))
            if id_col in ids_vistos:
                errores.append(ValidationError(ruta_relativa, f"{prefijo}.id", f"duplicado: {id_col!r}"))
            ids_vistos.append(id_col)

        for campo_str, min_len, max_len in (
            ("titulo", 3, 120),
            ("descripcion", 10, 300),
            ("icono", 1, 40),
        ):
            v = col.get(campo_str)
            if v is not None and (not isinstance(v, str) or not (min_len <= len(v) <= max_len)):
                errores.append(ValidationError(ruta_relativa, f"{prefijo}.{campo_str}", f"{min_len}–{max_len}"))

        orden = col.get("orden")
        if orden is not None:
            if isinstance(orden, bool) or not isinstance(orden, int) or orden < 0:
                errores.append(ValidationError(ruta_relativa, f"{prefijo}.orden", "entero ≥ 0 (no bool)"))

    if set(ids_vistos) != set(COLUMNAS_VALIDAS):
        faltan = set(COLUMNAS_VALIDAS) - set(ids_vistos)
        if faltan:
            errores.append(ValidationError(ruta_relativa, "columnas", f"faltan: {sorted(faltan)}"))

    return ColumnasConfig(ruta=ruta, datos=datos, columnas=lista), errores
