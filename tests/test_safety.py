"""Pruebas de seguridad de rutas y recorrido."""
from __future__ import annotations
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from lib.safety import es_ruta_segura, iterar_arbol_seguro

class TestSafety(unittest.TestCase):
    def test_ruta_relativa_se_resuelve_desde_raiz(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "sub").mkdir(); (root / "sub" / "a.txt").write_text("ok")
            self.assertEqual(es_ruta_segura(root, Path("sub/a.txt")), (True, ""))

    def test_ruta_absoluta_dentro_de_raiz(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); f = root / "a.txt"; f.write_text("ok")
            self.assertEqual(es_ruta_segura(root, f)[0], True)

    def test_ruta_fuera_de_raiz_rechazada(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as other:
            root = Path(td); f = Path(other) / "x.txt"; f.write_text("x")
            self.assertFalse(es_ruta_segura(root, f)[0])

    def test_ruta_relativa_con_parent_rechazada(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(es_ruta_segura(Path(td), Path("../escape"))[0])

    @unittest.skipUnless(hasattr(os, "symlink") and os.name != "nt", "symlink no disponible")
    def test_symlink_en_ancestro_de_raiz_rechazado(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); real = base / "real"; real.mkdir(); link = base / "link"; link.symlink_to(real, target_is_directory=True)
            self.assertFalse(es_ruta_segura(link, Path("archivo"))[0])

    def test_os_walk_onerror_se_reporta(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            error = PermissionError("acceso denegado"); error.filename = str(root / "privado")
            with mock.patch("lib.safety.os.walk", side_effect=lambda *a, **kw: kw["onerror"](error) or iter(())):
                archivos, errores = iterar_arbol_seguro(root)
            self.assertEqual(archivos, [])
            self.assertTrue(any("no se pudo leer" in e.mensaje for e in errores))

if __name__ == "__main__":
    unittest.main()
