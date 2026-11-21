"""Pruebas de rutas relativas del módulo global CIBA."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from build_catalog import _conectar_sistema_global  # noqa: E402


class TestRutasScriptGlobal(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.js = self.root / "assets" / "js" / "ciba-global.js"
        self.js.parent.mkdir(parents=True)
        self.js.write_text("/* global */", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def comprobar(self, ruta: str, esperado: str) -> None:
        pagina = self.root / ruta / "index.html"
        pagina.parent.mkdir(parents=True, exist_ok=True)
        pagina.write_text(
            '<!doctype html><html><head></head><body>'
            '<script type="module" src="../../../assets/js/ciba-global.js?v=antigua"></script>'
            '</body></html>',
            encoding="utf-8",
        )
        errores = _conectar_sistema_global(pagina, self.root)
        self.assertEqual(errores, [])
        html = pagina.read_text(encoding="utf-8")
        self.assertIn(f'src="{esperado}?v=20261121-05"', html)

    def test_corrige_ruta_en_pagina_de_columna(self) -> None:
        self.comprobar("i/I1", "../../assets/js/ciba-global.js")

    def test_corrige_ruta_en_articulo_profundo(self) -> None:
        self.comprobar("b/B1/B1-02/B1-02-01", "../../../../assets/js/ciba-global.js")


if __name__ == "__main__":
    unittest.main()
