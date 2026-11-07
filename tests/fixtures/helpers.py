"""Helpers para construir repositorios temporales de prueba."""

from __future__ import annotations

import json
import os
from pathlib import Path

COLUMNAS_JSON = {
    "version": 1,
    "columnas": [
        {"id": "C", "titulo": "Crianza", "descripcion": "x" * 20, "orden": 1, "icono": "c"},
        {"id": "I", "titulo": "Internet", "descripcion": "x" * 20, "orden": 2, "icono": "i"},
        {"id": "B", "titulo": "Bienestar", "descripcion": "x" * 20, "orden": 3, "icono": "b"},
        {"id": "A", "titulo": "Acompañamiento", "descripcion": "x" * 20, "orden": 4, "icono": "a"},
    ],
}


def _escribir_json(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def area_ok(id_area: str, col: str, orden: int = 1) -> dict:
    return {
        "id": id_area,
        "titulo": f"Área {id_area}",
        "descripcion": "Descripción de área de prueba suficientemente larga.",
        "columna": col,
        "orden": orden,
    }


def meta_ok(id_pagina: str, col: str, area: str, *, estado: str = "publicado",
            mostrar_col: bool = True, mostrar_area: bool = True,
            fecha: str = "2026-01-01") -> dict:
    return {
        "id": id_pagina,
        "titulo": f"Página {id_pagina}",
        "descripcion": "Descripción de página de prueba suficientemente larga.",
        "columna": col,
        "area": area,
        "palabras_clave": ["prueba", "ciba"],
        "estado": estado,
        "fecha_publicacion": fecha,
        "mostrar_en_columna": mostrar_col,
        "mostrar_en_area": mostrar_area,
    }


def crear_repo(tmp: Path, columnas_datos: dict | None = None) -> Path:
    content = tmp / "content"
    esquema = content / "_esquema"
    _escribir_json(esquema / "columnas.json", columnas_datos or COLUMNAS_JSON)
    _escribir_json(esquema / "meta.schema.json", {"$schema": "https://json-schema.org/draft/2020-12/schema"})
    _escribir_json(esquema / "area.schema.json", {"$schema": "https://json-schema.org/draft/2020-12/schema"})
    for letra in ("c", "i", "b", "a"):
        (content / letra).mkdir(parents=True, exist_ok=True)
    return content


def añadir_area(content: Path, col: str, id_area: str, datos_area: dict | None = None) -> Path:
    ruta = content / col.lower() / id_area
    _escribir_json(ruta / "area.json", datos_area or area_ok(id_area, col.upper()))
    return ruta


def añadir_pagina(content: Path, col: str, id_area: str, id_pagina: str,
                 meta: dict | None = None, *, con_index: bool = True,
                 tamano_index: int = 300) -> Path:
    ruta = content / col.lower() / id_area / id_pagina
    _escribir_json(ruta / "meta.json", meta or meta_ok(id_pagina, col.upper(), id_area))
    ruta.mkdir(parents=True, exist_ok=True)
    if con_index:
        (ruta / "index.html").write_text("x" * tamano_index, encoding="utf-8")
    return ruta


def añadir_foto(pagina_dir: Path, ruta_relativa: str, contenido: bytes = b"\x89PNG\r\n\x1a\n") -> Path:
    destino = pagina_dir / ruta_relativa
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    return destino


def crear_symlink(origen: Path, destino: Path) -> bool:
    """Crea un symlink origen→destino. Devuelve False si el SO no lo permite."""
    try:
        if destino.exists() or destino.is_symlink():
            destino.unlink()
        os.symlink(origen, destino)
        return True
    except (OSError, NotImplementedError):
        return False


def tiene_symlinks() -> bool:
    return hasattr(os, "symlink") and os.name != "nt"
