"""Regresión: el menú global no debe borrar cabeceras editoriales."""
from pathlib import Path
import unittest

RAIZ = Path(__file__).resolve().parent.parent


class TestPreservacionCabecerasEditoriales(unittest.TestCase):
    def test_cabeceras_dentro_de_articulos_se_conservan(self) -> None:
        js = (RAIZ / "assets" / "js" / "ciba-global.js").read_text(encoding="utf-8")
        self.assertIn("if (!anterior.closest('.ciba-articulo')) anterior.remove();", js)
        self.assertIn("if (!anterior.closest('.ciba-articulo') && anterior.querySelector('a.marca')) anterior.remove();", js)

    def test_cabecera_de_gestacion_sigue_en_fuente(self) -> None:
        for codigo, titulo in (
            ("C1-06", "Comer durante el embarazo cuando los recursos son limitados"),
            ("C1-10", "Náuseas, vómitos, acidez y estreñimiento durante el embarazo"),
        ):
            html = (RAIZ / "content" / "c" / "C1" / codigo / "index.html").read_text(encoding="utf-8")
            self.assertIn(f"<h1>{titulo}</h1>", html)
            self.assertIn('<header class="cabecera">', html)


if __name__ == "__main__":
    unittest.main()
