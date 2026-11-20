"""Pruebas del auditor de enlaces internos CIBA."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from audit_internal_links import auditar  # noqa: E402


class TestAuditoriaEnlaces(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def escribir(self, ruta: str, html: str) -> None:
        destino = self.root / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(html, encoding="utf-8")

    def test_resuelve_rutas_relativas_y_directorios(self) -> None:
        self.escribir("c/index.html", '<a href="../i/">Informática</a><a href="articulo/index.html">Artículo</a>')
        self.escribir("i/index.html", "<h1>Informática</h1>")
        self.escribir("c/articulo/index.html", "<h1>Artículo</h1>")
        resultado = auditar(self.root)
        self.assertEqual(resultado["total_errores"], 0)
        self.assertEqual(resultado["enlaces_locales_revisados"], 2)

    def test_detecta_archivo_y_fragmento_ausentes(self) -> None:
        self.escribir("index.html", '<a href="no-existe.html">X</a><a href="#ausente">Y</a>')
        resultado = auditar(self.root)
        self.assertEqual(resultado["total_errores"], 2)
        self.assertEqual(
            {e["motivo"] for e in resultado["errores"]},
            {"Archivo o ruta no encontrado", "Fragmento no encontrado"},
        )

    def test_detecta_fragmento_en_otro_documento(self) -> None:
        self.escribir("index.html", '<a href="destino.html#seccion">Ir</a>')
        self.escribir("destino.html", '<section id="otra"></section>')
        resultado = auditar(self.root)
        self.assertEqual(resultado["total_errores"], 1)
        self.assertEqual(resultado["errores"][0]["motivo"], "Fragmento no encontrado en destino")

    def test_omite_enlaces_externos_y_reconoce_base_github_pages(self) -> None:
        self.escribir("index.html", '<a href="https://example.org">Externo</a><a href="https://ciba1000dias-lab.github.io/ciba2.0/c/">C</a>')
        self.escribir("c/index.html", "<h1>C</h1>")
        resultado = auditar(self.root, "https://ciba1000dias-lab.github.io/ciba2.0/")
        self.assertEqual(resultado["total_errores"], 0)
        self.assertEqual(resultado["enlaces_externos_omitidos"], 1)


if __name__ == "__main__":
    unittest.main()
