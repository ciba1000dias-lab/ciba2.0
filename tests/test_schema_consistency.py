"""Consistencia entre esquemas JSON (contratos) y validadores Python (ejecutables).

Los esquemas NO se ejecutan. Este test verifica que sus valores declarados
coincidan con los del código Python para detectar divergencias.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from lib import area_reader, columnas_reader, meta_reader  # noqa: E402
from lib.paths import COLUMNAS_VALIDAS, ESTADOS_VALIDOS  # noqa: E402


class TestConsistencia(unittest.TestCase):
    def setUp(self) -> None:
        self.esquema = RAIZ / "content" / "_esquema"

    def _leer(self, nombre: str) -> dict:
        return json.loads((self.esquema / nombre).read_text(encoding="utf-8"))

    def test_meta_estados_coinciden(self) -> None:
        schema = self._leer("meta.schema.json")
        enum_schema = schema["properties"]["estado"]["enum"]
        self.assertEqual(set(enum_schema), set(ESTADOS_VALIDOS))

    def test_meta_columnas_coinciden(self) -> None:
        schema = self._leer("meta.schema.json")
        enum_schema = schema["properties"]["columna"]["enum"]
        self.assertEqual(set(enum_schema), set(COLUMNAS_VALIDAS))

    def test_meta_longitudes_coinciden(self) -> None:
        schema = self._leer("meta.schema.json")
        self.assertEqual(schema["properties"]["titulo"]["minLength"], 3)
        self.assertEqual(schema["properties"]["titulo"]["maxLength"], 120)
        self.assertEqual(schema["properties"]["descripcion"]["minLength"], 10)
        self.assertEqual(schema["properties"]["descripcion"]["maxLength"], 300)

    def test_area_columnas_coinciden(self) -> None:
        schema = self._leer("area.schema.json")
        self.assertEqual(set(schema["properties"]["columna"]["enum"]), set(COLUMNAS_VALIDAS))

    def test_columnas_json_ids_oficiales(self) -> None:
        datos = self._leer("columnas.json")
        ids = {c["id"] for c in datos["columnas"]}
        self.assertEqual(ids, set(COLUMNAS_VALIDAS))

    def test_meta_campos_obligatorios_sincronizados(self) -> None:
        schema = self._leer("meta.schema.json")
        self.assertEqual(set(schema["required"]), set(meta_reader.CAMPOS_OBLIGATORIOS))

    def test_area_campos_obligatorios_sincronizados(self) -> None:
        schema = self._leer("area.schema.json")
        self.assertEqual(set(schema["required"]), set(area_reader.CAMPOS_OBLIGATORIOS))


if __name__ == "__main__":
    unittest.main()
