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
        area_generada = self.out / "c" / "C1" / "index.html"
        self.assertTrue(area_generada.is_file())
        self.assertIn("Este espacio forma parte de CIBA", area_generada.read_text(encoding="utf-8"))

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
        area = añadir_area(self.content, "c", "C3")
        (area / "index.html").write_text("<h1>Área</h1>", encoding="utf-8")
        pag = añadir_pagina(self.content, "c", "C3", "C3-01")
        pdf = self.content / "c" / "C3" / "guia-prueba.pdf"
        pdf.write_bytes(b"%PDF-1.4\\ncontenido de prueba")
        (pag / "archivo-privado.txt").write_text("no autorizado", encoding="utf-8")
        self.assertEqual(construir(self.content, self.out), 0)
        self.assertEqual(
            (self.out / "c" / "C3" / "guia-prueba.pdf").read_bytes(),
            pdf.read_bytes(),
        )
        self.assertFalse((self.out / "c" / "C3" / "C3-01" / "archivo-privado.txt").exists())

    def test_pdf_con_firma_invalida_falla_build(self) -> None:
        añadir_area(self.content, "c", "C3")
        pag = añadir_pagina(self.content, "c", "C3", "C3-01")
        (pag / "guia-invalida.pdf").write_bytes(b"<html>no es pdf")
        self.assertEqual(construir(self.content, self.out), 1)
        self.assertFalse((self.out / "c" / "C3" / "C3-01" / "guia-invalida.pdf").exists())

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


    def test_subseccion_archivada_tiene_pagina_propia_y_catalogo(self) -> None:
        añadir_area(self.content, "b", "B1")
        subseccion = self.content / "b" / "B1" / "B1-01"
        subseccion.mkdir(parents=True)
        meta_sub = meta_ok("B1-01", "B", "B1", estado="archivado")
        meta_sub["titulo"] = "Subsección de prueba"
        meta_sub["descripcion"] = "Organiza artículos publicados de una misma temática."
        (subseccion / "meta.json").write_text(
            json.dumps(meta_sub, ensure_ascii=False), encoding="utf-8"
        )
        articulo = subseccion / "B1-01-01"
        articulo.mkdir()
        meta_art = meta_ok("B1-01-01", "B", "B1")
        meta_art["titulo"] = "Artículo de prueba"
        (articulo / "meta.json").write_text(
            json.dumps(meta_art, ensure_ascii=False), encoding="utf-8"
        )
        (articulo / "index.html").write_text("<html><body>" + ("x" * 300) + "</body></html>", encoding="utf-8")

        self.assertEqual(construir(self.content, self.out), 0)
        pagina_sub = self.out / "b" / "B1" / "B1-01" / "index.html"
        self.assertTrue(pagina_sub.is_file())
        html_sub = pagina_sub.read_text(encoding="utf-8")
        self.assertIn("Subsección de prueba", html_sub)
        self.assertIn("Artículo de prueba", html_sub)
        self.assertIn("B1-01-01/", html_sub)
        catalogo = self._leer_catalogo()
        self.assertEqual([s["id"] for s in catalogo["subsecciones"]], ["B1-01"])
        self.assertEqual([p["id"] for p in catalogo["paginas"]], ["B1-01-01"])
        self.assertTrue((self.out / "b" / "index.html").is_file())

    def test_publica_articulo_anidado_en_subseccion(self) -> None:
        añadir_area(self.content, "b", "B1")
        subseccion = self.content / "b" / "B1" / "B1-01"
        subseccion.mkdir(parents=True)
        meta_sub = meta_ok("B1-01", "B", "B1", estado="archivado")
        (subseccion / "meta.json").write_text(
            json.dumps(meta_sub, ensure_ascii=False), encoding="utf-8"
        )

        articulo = subseccion / "B1-01-01"
        articulo.mkdir()
        meta_art = meta_ok("B1-01-01", "B", "B1")
        (articulo / "meta.json").write_text(
            json.dumps(meta_art, ensure_ascii=False), encoding="utf-8"
        )
        (articulo / "index.html").write_text("x" * 300, encoding="utf-8")

        self.assertEqual(construir(self.content, self.out), 0)
        ruta = self.out / "b" / "B1" / "B1-01" / "B1-01-01"
        self.assertTrue((ruta / "index.html").is_file())
        self.assertEqual(
            self._leer_catalogo()["paginas"][0]["ruta_publica"],
            "b/B1/B1-01/B1-01-01/",
        )


    def test_unifica_identidad_azul_en_paginas_interiores_informatica(self) -> None:
        raiz = self.tmp / "dist"
        articulo = raiz / "i" / "I1" / "I1-01" / "index.html"
        articulo.parent.mkdir(parents=True)
        contenido = '<!doctype html><html><head><style>.hero{background:#493a32}</style></head><body><header class="hero">INFORMÁTICA</header></body></html>'

        normalizado = build_catalog._normalizar_estilo_informatica(contenido, articulo, raiz)
        self.assertIn("data-ciba-informatica-unificacion", normalizado)
        self.assertIn("linear-gradient(120deg,#12364d 0%,#174f70 58%,#206b88 100%)", normalizado)

        portada = raiz / "i" / "index.html"
        self.assertEqual(
            build_catalog._normalizar_estilo_informatica(contenido, portada, raiz),
            contenido,
        )

    def test_informatica_normaliza_area_y_articulo_sin_perder_recursos(self) -> None:
        raiz = self.tmp / "dist"
        contenido = (
            '<!doctype html><html><head></head><body>'
            '<header class="hero"><h1>Contenido aprobado</h1></header>'
            '<figure><svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg></figure>'
            '<audio controls src="voz.mp3"></audio>'
            '<div class="interactive">Actividad interactiva</div>'
            '</body></html>'
        )
        for ruta in ("i/I3/index.html", "i/I3/I3-02/index.html"):
            pagina = raiz / ruta
            pagina.parent.mkdir(parents=True, exist_ok=True)
            normalizado = build_catalog._normalizar_estilo_informatica(contenido, pagina, raiz)
            self.assertIn("data-ciba-informatica-unificacion", normalizado)
            self.assertIn("linear-gradient(120deg,#12364d 0%,#174f70 58%,#206b88 100%)", normalizado)
            self.assertIn("Contenido aprobado", normalizado)
            self.assertIn('src="voz.mp3"', normalizado)
            self.assertIn("Actividad interactiva", normalizado)
            self.assertIn("<svg", normalizado)
            self.assertEqual(
                normalizado,
                build_catalog._normalizar_estilo_informatica(normalizado, pagina, raiz),
            )

        externa = raiz / "c/C1/C1-01/index.html"
        self.assertEqual(
            build_catalog._normalizar_estilo_informatica(contenido, externa, raiz),
            contenido,
        )

    def test_normaliza_migas_y_metadatos_de_articulos(self) -> None:
        añadir_area(self.content, "c", "C1")
        area = self.content / "c" / "C1"
        (area / "index.html").write_text("<html><body>" + ("a" * 250) + "</body></html>", encoding="utf-8")
        articulo = añadir_pagina(self.content, "c", "C1", "C1-01")
        (self.tmp / "index.html").write_text("<!doctype html><html><body>CIBA</body></html>", encoding="utf-8")
        css = self.tmp / "assets" / "css" / "ciba-global.css"
        js = self.tmp / "assets" / "js" / "ciba-global.js"
        css.parent.mkdir(parents=True, exist_ok=True)
        js.parent.mkdir(parents=True, exist_ok=True)
        css.write_text("/* CSS global de prueba */", encoding="utf-8")
        js.write_text('/* ciba-global.css?v=20261112-08 */', encoding="utf-8")

        self.assertEqual(construir(self.content, self.out), 0)
        pagina = self.out / "c" / "C1" / "C1-01" / "index.html"
        html = pagina.read_text(encoding="utf-8")
        self.assertIn("<title>Página C1-01 | Crianza · CIBA</title>", html)
        self.assertIn('name="description" content="Descripción de página de prueba suficientemente larga."', html)
        self.assertIn('data-ciba-migas', html)
        self.assertIn("Página C1-01", html)
        self.assertIn('href="../../../index.html"', html)
        self.assertIn('href="../../index.html"', html)
        self.assertIn('href="../index.html"', html)
        self.assertIn("ciba-global.js?v=20261119-01", html)
        portada = (self.out / "c" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-ciba-migas', portada)
        self.assertIn("Crianza", portada)


    def test_sistema_editorial_comun_respeta_paletas_de_las_cuatro_columnas(self) -> None:
        raiz = self.tmp / "dist"
        colores = {
            "c": "#172b27",
            "i": "#12364d",
            "b": "#493a32",
            "a": "#493a32",
        }
        for letra, color in colores.items():
            pagina = raiz / letra / "AREA" / "index.html"
            pagina.parent.mkdir(parents=True, exist_ok=True)
            html = "<!doctype html><html><head></head><body><h1>Prueba</h1></body></html>"
            normalizado = build_catalog._normalizar_sistema_editorial(html, pagina, raiz)
            self.assertIn("data-ciba-sistema-editorial", normalizado)
            self.assertIn(f"--ciba-color-primario: {color}", normalizado)
            self.assertIn("--ciba-font-display: Georgia", normalizado)
            self.assertIn("prefers-reduced-motion: reduce", normalizado)

    def test_sistema_editorial_es_idempotente_y_no_afecta_paginas_externas(self) -> None:
        raiz = self.tmp / "dist"
        pagina = raiz / "i" / "I1" / "index.html"
        pagina.parent.mkdir(parents=True, exist_ok=True)
        html = "<html><body><h1>Prueba</h1></body></html>"
        primero = build_catalog._normalizar_sistema_editorial(html, pagina, raiz)
        segundo = build_catalog._normalizar_sistema_editorial(primero, pagina, raiz)
        self.assertEqual(primero, segundo)
        externa = raiz / "plataforma" / "index.html"
        self.assertEqual(build_catalog._normalizar_sistema_editorial(html, externa, raiz), html)


    def test_crianza_estandariza_paginas_interiores_y_conserva_contenido(self) -> None:
        raiz = self.tmp / "dist"
        articulo = raiz / "c" / "C3" / "C3-05" / "index.html"
        articulo.parent.mkdir(parents=True)
        html = '<!doctype html><html><head></head><body><article class="ciba-articulo"><h1>Contenido aprobado</h1><img src="foto.webp" alt="Foto"><div class="interactivo">Actividad</div></article></body></html>'
        normalizado = build_catalog._normalizar_crianza(html, articulo, raiz)
        self.assertIn("data-ciba-crianza-estandar", normalizado)
        self.assertIn("--ciba-crianza-verde: #526e56", normalizado)
        self.assertIn("Contenido aprobado", normalizado)
        self.assertIn('src="foto.webp"', normalizado)
        self.assertIn("Actividad", normalizado)
        self.assertIn("prefers-reduced-motion: reduce", normalizado)

    def test_crianza_estandar_es_idempotente_y_no_afecta_otras_columnas(self) -> None:
        raiz = self.tmp / "dist"
        pagina = raiz / "c" / "C1" / "index.html"
        pagina.parent.mkdir(parents=True)
        html = "<html><body><h1>Prueba</h1></body></html>"
        primero = build_catalog._normalizar_crianza(html, pagina, raiz)
        self.assertEqual(primero, build_catalog._normalizar_crianza(primero, pagina, raiz))
        informatica = raiz / "i" / "I1" / "index.html"
        self.assertEqual(build_catalog._normalizar_crianza(html, informatica, raiz), html)


if __name__ == "__main__":
    unittest.main()
