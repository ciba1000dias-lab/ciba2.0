"""Lectura y validación del area.json de cada área."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .paths import RE_AREA, COLUMNAS_VALIDAS

CAMPOS_OBLIGATORIOS = ("id", "titulo", "descripcion", "columna", "orden")


@dataclass
class AreaMeta:
    ruta_relativa: str
    ruta_fisica: Path
    datos: dict[str, Any] = field(default_factory=dict)


def leer_area(ruta_area: Path, ruta_relativa: str) -> tuple[AreaMeta | None, list[ValidationError]]:
    errores: list[ValidationError] = []
    if ruta_area.is_symlink():
        errores.append(ValidationError(ruta_relativa, "area.json", "es symlink"))
        return None, errores
    if not ruta_area.is_file():
        errores.append(ValidationError(ruta_relativa, "area.json", "archivo ausente"))
        return None, errores

    try:
        datos = json.loads(ruta_area.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errores.append(ValidationError(ruta_relativa, "area.json", f"JSON inválido: {exc}"))
        return None, errores

    if not isinstance(datos, dict):
        errores.append(ValidationError(ruta_relativa, "area.json", "debe ser objeto JSON"))
        return None, errores

    extra = set(datos.keys()) - set(CAMPOS_OBLIGATORIOS) - set(CAMPOS_OPCIONALES)
    if extra:
        errores.append(ValidationError(ruta_relativa, "area.json", f"campos desconocidos: {sorted(extra)}"))

    for campo in CAMPOS_OPCIONALES:
        if campo in datos:
            valor = datos[campo]
            limite = 80 if campo == "estructura" else 40
            if not isinstance(valor, str) or not (3 <= len(valor) <= limite):
                errores.append(ValidationError(ruta_relativa, campo, f"string de 3–{limite} caracteres"))

    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in datos:
            errores.append(ValidationError(ruta_relativa, campo, "campo obligatorio ausente"))
        elif datos[campo] is None:
            errores.append(ValidationError(ruta_relativa, campo, "no puede ser null"))

    id_area = datos.get("id")
    if id_area is not None:
        if not isinstance(id_area, str):
            errores.append(ValidationError(ruta_relativa, "id", "debe ser string"))
        elif not re.match(RE_AREA, id_area):
            errores.append(ValidationError(ruta_relativa, "id", f"formato inválido: {id_area!r}"))

    col = datos.get("columna")
    if col is not None and col not in COLUMNAS_VALIDAS:
        errores.append(ValidationError(ruta_relativa, "columna", f"valor inválido: {col!r}"))

    titulo = datos.get("titulo")
    if titulo is not None and (not isinstance(titulo, str) or not (3 <= len(titulo) <= 120)):
        errores.append(ValidationError(ruta_relativa, "titulo", "3–120 caracteres"))

    descripcion = datos.get("descripcion")
    if descripcion is not None and (not isinstance(descripcion, str) or not (10 <= len(descripcion) <= 300)):
        errores.append(ValidationError(ruta_relativa, "descripcion", "10–300 caracteres"))

    orden = datos.get("orden")
    if orden is not None:
        if isinstance(orden, bool) or not isinstance(orden, int) or orden < 0:
            errores.append(ValidationError(ruta_relativa, "orden", "entero ≥ 0 (no bool)"))

    return AreaMeta(ruta_relativa=ruta_relativa, ruta_fisica=ruta_area, datos=datos), errores
