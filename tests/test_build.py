"""Pruebas del generador de catálogo CIBA."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import build_catalog  # noqa: E402
from build_catalog import construir  # noqa: E402
from tests.fixtures.helpers import (  # noqa: E402
    añadir_area, añadir_foto, añadir_pagina, crear_repo, crear_symlink, meta_ok,
    tiene_symlinks,
)


class TestBuild(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.content = crear_repo(self.tmp)
        self.out = self.tmp / "dist"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _leer_catalogo(self) -> dict:
        return json.loads((self.out / "data" / "catalogo.json").read_text(encoding="utf-8"))

    # ---------- estructura básica ----------

    def test_01_sin_paginas(self) -> None:
        self.assertEqual(construir(self.content, self.out), 0)
        cat = self._leer_catalogo()
        self.assertEqual(cat["paginas"], [])
        self.assertEqual(cat["areas"], [])
        self.assertEqual({c["id"] for c in cat["columnas"]}, {"C", "I", "B", "A"})

    def test_02_una_pagina_valida(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        self.assertEqual(construir(self.content, self.out), 0)
        cat = self._leer_catalogo()
        self.assertEqual(len(cat["paginas"]), 1)
        ruta = self.out / "c" / "C1" / "C1-01"
        self.assertTrue((ruta / "index.html").is_file())
        self.assertFalse((ruta / "meta.json").exists())
        self.assertFalse((self.out / "c" / "C1" / "area.json").exists())

    def test_area_sin_paginas_aparece_en_catalogo(self) -> None:
        añadir_area(self.content, "c", "C1")
        self.assertEqual(construir(self.content, self.out), 0)
        cat = self._leer_catalogo()
        self.assertEqual([a["id"] for a in cat["areas"]], ["C1"])

    def test_area_con_varias_paginas_no_duplicada(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        añadir_pagina(self.content, "c", "C1", "C1-02")
        añadir_pagina(self.content, "c", "C1", "C1-03")
        self.assertEqual(construir(self.content, self.out), 0)
        cat = self._leer_catalogo()
        self.assertEqual([a["id"] for a in cat["areas"]], ["C1"])
        self.assertEqual(len(cat["paginas"]), 3)

    def test_varias_areas_y_columnas(self) -> None:
        for letra, area in (("c", "C1"), ("c", "C2"), ("i", "I1"), ("b", "B1"), ("a", "A1")):
            añadir_area(self.content, letra, area)
            añadir_pagina(self.content, letra, area, f"{area}-01")
        self.assertEqual(construir(self.content, self.out), 0)
        cat = self._leer_catalogo()
        self.assertEqual(sorted(a["id"] for a in cat["areas"]), ["A1", "B1", "C1", "C2", "I1"])

    # ---------- allowlist ----------

    def test_archivos_privados_no_se_copian(self) -> None:
        añadir_area(self.content, "c", "C1")
        pag = añadir_pagina(self.content, "c", "C1", "C1-01")
        (pag / "privado.txt").write_text("secreto", encoding="utf-8")
        (pag / "borrador.html").write_text("<p>borrador</p>", encoding="utf-8")
        (pag / "media").mkdir(exist_ok=True)
        (pag / "media" / "no_declarada.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        self.assertEqual(construir(self.content, self.out), 0)
        destino = self.out / "c" / "C1" / "C1-01"
        self.assertTrue((destino / "index.html").is_file())
        self.assertFalse((destino / "privado.txt").exists())
        self.assertFalse((destino / "borrador.html").exists())
        self.assertFalse((destino / "media" / "no_declarada.png").exists())

    def test_solo_media_declarada_se_copia(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["media"] = {"fotos": [{"ruta": "media/ok.png"}]}
        pag = añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        añadir_foto(pag, "media/ok.png")
        añadir_foto(pag, "media/otra.png")
        self.assertEqual(construir(self.content, self.out), 0)
        destino = self.out / "c" / "C1" / "C1-01"
        self.assertTrue((destino / "media" / "ok.png").is_file())
        self.assertFalse((destino / "media" / "otra.png").exists())

    def test_pdf_valido_se_publica_y_se_conserva_la_allowlist(self) -> None:
        añadir_area(self.content, "c", "C3")
        pag = añadir_pagina(self.content, "c", "C3", "C3-01")
        pdf = self.content / "c" / "C3" / "guia-prueba.pdf"
        pdf.write_bytes(b"%PDF-1.4\\ncontenido de prueba")
        (pag / "archivo-privado.pdf").write_bytes(b"%PDF-1.4\\nno autorizado")
        self.assertEqual(construir(self.content, self.out), 0)
        self.assertEqual(
            (self.out / "c" / "C3" / "guia-prueba.pdf").read_bytes(),
            pdf.read_bytes(),
        )
        self.assertFalse((self.out / "c" / "C3" / "C3-01" / "archivo-privado.pdf").exists())

    def test_pdf_con_firma_invalida_falla_build(self) -> None:
        añadir_area(self.content, "c", "C3")
        añadir_pagina(self.content, "c", "C3", "C3-01")
        (self.content / "c" / "C3" / "guia-invalida.pdf").write_bytes(b"<html>no es pdf")
        self.assertEqual(construir(self.content, self.out), 1)
        self.assertFalse((self.out / "c" / "C3" / "guia-invalida.pdf").exists())

    def test_scripts_y_docs_no_se_copian(self) -> None:
        (self.tmp / "scripts").mkdir()
        (self.tmp / "scripts" / "secreto.py").write_text("# interno", encoding="utf-8")
        (self.tmp / "docs").mkdir()
        (self.tmp / "docs" / "nota.md").write_text("# interno", encoding="utf-8")
        self.assertEqual(construir(self.content, self.out), 0)
        self.assertFalse((self.out / "scripts").exists())
        self.assertFalse((self.out / "docs").exists())

    def test_portada_se_copia_a_dist(self) -> None:
        (self.tmp / "index.html").write_text("<h1>CIBA</h1>", encoding="utf-8")
        self.assertEqual(construir(self.content, self.out), 0)
        self.assertEqual((self.out / "index.html").read_text(encoding="utf-8"), "<h1>CIBA</h1>")

    def test_assets_se_copian(self) -> None:
        (self.tmp / "assets").mkdir()
        (self.tmp / "assets" / "x.txt").write_text("hola", encoding="utf-8")
        self.assertEqual(construir(self.content, self.out), 0)
        self.assertTrue((self.out / "assets" / "x.txt").is_file())

    def test_ningun_externo_termina_en_dist(self) -> None:
        # archivo fuera de content y assets
        externo = self.tmp / "fuera.txt"
        externo.write_text("no debe publicarse", encoding="utf-8")
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        self.assertEqual(construir(self.content, self.out), 0)
        # buscar el contenido en dist
        for p in self.out.rglob("*"):
            if p.is_file():
                self.assertNotEqual(p.read_text(errors="ignore"), "no debe publicarse")

    # ---------- visibilidad ----------

    def test_flags_visibilidad(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01",
                      meta=meta_ok("C1-01", "C", "C1", mostrar_col=False, mostrar_area=True))
        self.assertEqual(construir(self.content, self.out), 0)
        p = self._leer_catalogo()["paginas"][0]
        self.assertFalse(p["mostrar_en_columna"])
        self.assertTrue(p["mostrar_en_area"])

    def test_borrador_no_publicado(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01",
                      meta=meta_ok("C1-01", "C", "C1", estado="borrador"), con_index=False)
        self.assertEqual(construir(self.content, self.out), 0)
        self.assertEqual(self._leer_catalogo()["paginas"], [])

    # ---------- errores ----------

    def test_error_validacion_no_genera(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01", con_index=False)
        self.assertEqual(construir(self.content, self.out), 1)
        self.assertFalse((self.out / "data" / "catalogo.json").exists())

    def test_conserva_catalogo_anterior_si_falla(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        self.assertEqual(construir(self.content, self.out), 0)
        self.assertEqual(len(self._leer_catalogo()["paginas"]), 1)
        añadir_pagina(self.content, "c", "C1", "C1-02", con_index=False)
        self.assertEqual(construir(self.content, self.out), 1)
        cat = self._leer_catalogo()
        self.assertEqual(len(cat["paginas"]), 1)

    def test_fallo_instalacion_restaura_anterior(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        self.assertEqual(construir(self.content, self.out), 0)
        añadir_area(self.content, "c", "C2")
        añadir_pagina(self.content, "c", "C2", "C2-01")

        real_replace = build_catalog.os.replace

        def replace_falso(src, dst):
            src_s, dst_s = str(src), str(dst)
            if dst_s.endswith("dist") and src_s.endswith("dist.tmp"):
                raise OSError("fallo simulado")
            return real_replace(src, dst)

        with mock.patch.object(build_catalog.os, "replace", side_effect=replace_falso):
            self.assertEqual(construir(self.content, self.out), 1)

        ids = {p["id"] for p in self._leer_catalogo()["paginas"]}
        self.assertEqual(ids, {"C1-01"})
        self.assertFalse((self.tmp / "dist.old").exists())

    def test_error_seguridad_no_altera_catalogo(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        self.assertEqual(construir(self.content, self.out), 0)
        cat_inicial = self._leer_catalogo()

        # Introduce symlink en área C2
        if not tiene_symlinks():
            self.skipTest("SO sin symlinks")
        externo = self.tmp / "externo"
        externo.mkdir()
        self.assertTrue(crear_symlink(externo, self.content / "c" / "C2"))

        self.assertEqual(construir(self.content, self.out), 1)
        cat_final = self._leer_catalogo()
        self.assertEqual(cat_inicial, cat_final)



    def test_publica_paginas_auxiliares_sin_catalogarlas(self) -> None:
        añadir_area(self.content, "c", "C1")
        pagina = self.content / "c" / "C1" / "_paginas" / "alimentos" / "frutas"
        pagina.mkdir(parents=True)
        (pagina / "index.html").write_text(
            "<!doctype html><html><body>Biblioteca de frutas</body></html>",
            encoding="utf-8",
        )

        self.assertEqual(construir(self.content, self.out), 0)
        self.assertTrue(
            (self.out / "c" / "C1" / "alimentos" / "frutas" / "index.html").is_file()
        )
        self.assertEqual(self._leer_catalogo()["paginas"], [])


if __name__ == "__main__":
    unittest.main()
