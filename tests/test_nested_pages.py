"""Regresión: una página publicada puede contener artículos anidados."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from build_catalog import construir  # noqa: E402
from tests.fixtures.helpers import añadir_area, añadir_pagina, crear_repo, meta_ok  # noqa: E402


class TestPaginasAnidadas(unittest.TestCase):
    def test_publica_hijo_editorial_de_padre_publicado(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            content = crear_repo(raiz)
            añadir_area(content, "b", "B4")
            padre = añadir_pagina(
                content, "b", "B4", "B4-01",
                meta_ok("B4-01", "B", "B4", estado="publicado"),
            )
            hijo = padre / "B4-01-01"
            hijo.mkdir()
            (hijo / "meta.json").write_text(
                json.dumps(meta_ok("B4-01-01", "B", "B4"), ensure_ascii=False),
                encoding="utf-8",
            )
            (hijo / "index.html").write_text("x" * 350, encoding="utf-8")

            out = raiz / "dist"
            self.assertEqual(construir(content, out), 0)
            self.assertTrue((out / "b/B4/B4-01/B4-01-01/index.html").is_file())
            catalogo = json.loads((out / "data/catalogo.json").read_text(encoding="utf-8"))
            ids = {p["id"] for p in catalogo["paginas"]}
            self.assertIn("B4-01", ids)
            self.assertIn("B4-01-01", ids)


if __name__ == "__main__":
    unittest.main()
