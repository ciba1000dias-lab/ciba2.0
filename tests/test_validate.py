"""Pruebas del validador de contenidos CIBA."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from validate_content import validar  # noqa: E402
from tests.fixtures.helpers import (  # noqa: E402
    COLUMNAS_JSON, añadir_area, añadir_foto, añadir_pagina, area_ok, crear_repo,
    crear_symlink, meta_ok, tiene_symlinks,
)


class TestValidar(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.content = crear_repo(self.tmp)

    def tearDown(self) -> None:
        self._tmp.cleanup()


    def test_meta_rechaza_null_en_campo_obligatorio(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["titulo"] = None
        añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "titulo" and "null" in e.mensaje for e in errores))

    def test_area_rechaza_null_en_campo_obligatorio(self) -> None:
        datos = area_ok("C1", "C")
        datos["titulo"] = None
        añadir_area(self.content, "c", "C1", datos)
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "titulo" and "null" in e.mensaje for e in errores))

    def test_columnas_rechaza_null_en_campo_obligatorio(self) -> None:
        datos = json.loads(json.dumps(COLUMNAS_JSON))
        datos["columnas"][0]["titulo"] = None
        (self.content / "_esquema" / "columnas.json").write_text(json.dumps(datos), encoding="utf-8")
        errores = validar(self.content)
        self.assertTrue(any("null" in e.mensaje for e in errores))

    def test_fecha_no_acepta_mes_sin_cero(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1", fecha="2026-1-01")
        añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "fecha_publicacion" for e in errores))

    # ---------- estructura básica ----------

    def test_01_repo_sin_paginas(self) -> None:
        self.assertEqual(validar(self.content), [])

    def test_02_una_pagina_valida(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        self.assertEqual(validar(self.content), [])

    def test_03_varias_paginas_misma_area(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        añadir_pagina(self.content, "c", "C1", "C1-02")
        self.assertEqual(validar(self.content), [])

    def test_04_varias_areas_misma_columna(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_area(self.content, "c", "C2")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        añadir_pagina(self.content, "c", "C2", "C2-01")
        self.assertEqual(validar(self.content), [])

    def test_05_cuatro_columnas(self) -> None:
        for letra, area in (("c", "C1"), ("i", "I1"), ("b", "B1"), ("a", "A1")):
            añadir_area(self.content, letra, area)
            añadir_pagina(self.content, letra, area, f"{area}-01")
        self.assertEqual(validar(self.content), [])

    # ---------- identificadores ----------

    def test_06_id_duplicado(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        añadir_area(self.content, "c", "C2")
        añadir_pagina(self.content, "c", "C2", "C1-01", meta=meta_ok("C1-01", "C", "C2"))
        errores = validar(self.content)
        self.assertTrue(any("duplicado" in e.mensaje for e in errores))

    def test_area_id_no_coincide_con_carpeta(self) -> None:
        añadir_area(self.content, "c", "C2")
        (self.content / "c" / "C2" / "area.json").write_text(
            '{"id":"C1","titulo":"x","descripcion":"' + "y" * 20 + '","columna":"C","orden":1}',
            encoding="utf-8",
        )
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "id" for e in errores))

    def test_pagina_id_no_empieza_por_area(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C2-01", meta=meta_ok("C2-01", "C", "C1"))
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "id" for e in errores))

    # ---------- metadatos ----------

    def test_07_metadatos_ausentes(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        del meta["titulo"]
        añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "titulo" and "ausente" in e.mensaje for e in errores))

    def test_campo_desconocido_en_meta(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["campo_extra"] = "x"
        añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        errores = validar(self.content)
        self.assertTrue(any("desconocidos" in e.mensaje for e in errores))

    def test_fecha_futura(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01",
                      meta=meta_ok("C1-01", "C", "C1", fecha="2999-12-31"))
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "fecha_publicacion" for e in errores))

    def test_booleano_como_entero_no_aceptado(self) -> None:
        datos = area_ok("C1", "C")
        datos["orden"] = True
        añadir_area(self.content, "c", "C1", datos_area=datos)
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "orden" for e in errores))

    # ---------- estructura física ----------

    def test_08_area_sin_area_json(self) -> None:
        (self.content / "c" / "C1").mkdir(parents=True, exist_ok=True)
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "area.json" for e in errores))

    def test_09_publicada_sin_index(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01", con_index=False)
        errores = validar(self.content)
        self.assertTrue(any(e.campo == "index.html" for e in errores))

    def test_10_borrador(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01",
                      meta=meta_ok("C1-01", "C", "C1", estado="borrador"), con_index=False)
        self.assertEqual(validar(self.content), [])

    # ---------- multimedia ----------

    def test_media_ruta_insegura(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["media"] = {"fotos": [{"ruta": "../../etc/passwd"}]}
        añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        errores = validar(self.content)
        self.assertTrue(any("media.fotos" in e.campo for e in errores))

    def test_media_archivo_inexistente(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["media"] = {"fotos": [{"ruta": "media/no-existe.png"}]}
        añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        errores = validar(self.content)
        self.assertTrue(any("media.fotos" in e.campo for e in errores))

    def test_media_foto_valida(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["media"] = {"fotos": [{"ruta": "media/foto.png", "alt": "x"}]}
        pag = añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        añadir_foto(pag, "media/foto.png")
        self.assertEqual(validar(self.content), [])

    def test_enlaces_externos_invalidos(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["enlaces_externos"] = [{"titulo": "x", "url": "no-es-url"}]
        añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        errores = validar(self.content)
        self.assertTrue(any("enlaces_externos" in e.campo for e in errores))

    # ---------- columnas.json ----------

    def test_columnas_json_invalido(self) -> None:
        (self.content / "_esquema" / "columnas.json").write_text("{no-es-json", encoding="utf-8")
        errores = validar(self.content)
        self.assertTrue(any("json" in e.campo for e in errores))

    def test_columnas_faltante(self) -> None:
        datos = {"version": 1, "columnas": [c for c in COLUMNAS_JSON["columnas"] if c["id"] != "A"]}
        content = crear_repo(self.tmp / "otro", columnas_datos=datos)
        errores = validar(content)
        self.assertTrue(any(e.campo == "columnas" for e in errores))

    def test_columnas_duplicada(self) -> None:
        datos = json.loads(json.dumps(COLUMNAS_JSON))
        datos["columnas"].append({"id": "C", "titulo": "Duplicada", "descripcion": "x" * 20, "orden": 5, "icono": "x"})
        content = crear_repo(self.tmp / "otro", columnas_datos=datos)
        errores = validar(content)
        self.assertTrue(any("duplicado" in e.mensaje for e in errores))

    def test_columnas_raiz_campo_extra(self) -> None:
        datos = json.loads(json.dumps(COLUMNAS_JSON))
        datos["extra"] = "x"
        content = crear_repo(self.tmp / "otro", columnas_datos=datos)
        errores = validar(content)
        self.assertTrue(any("desconocidos" in e.mensaje for e in errores))

    def test_columnas_version_booleana(self) -> None:
        datos = json.loads(json.dumps(COLUMNAS_JSON))
        datos["version"] = True
        content = crear_repo(self.tmp / "otro", columnas_datos=datos)
        errores = validar(content)
        self.assertTrue(any(e.campo == "version" for e in errores))

    def test_columnas_tipo_incorrecto_en_columna(self) -> None:
        datos = json.loads(json.dumps(COLUMNAS_JSON))
        datos["columnas"][0]["titulo"] = 123
        content = crear_repo(self.tmp / "otro", columnas_datos=datos)
        errores = validar(content)
        self.assertTrue(any("titulo" in e.campo for e in errores))

    # ---------- columnas físicas ----------

    def test_columna_ausente(self) -> None:
        # Elimina content/a
        import shutil
        shutil.rmtree(self.content / "a")
        errores = validar(self.content)
        self.assertTrue(any("columna ausente" in e.mensaje for e in errores))

    def test_columna_duplicada_por_mayusculas(self) -> None:
        # Crea content/C además de content/c
        (self.content / "C").mkdir(parents=True, exist_ok=True)
        errores = validar(self.content)
        self.assertTrue(any("mayúsculas" in e.mensaje or "debe llamarse" in e.mensaje for e in errores))

    def test_columna_nombre_invalido(self) -> None:
        (self.content / "x").mkdir(parents=True, exist_ok=True)
        errores = validar(self.content)
        self.assertTrue(any("nombre de columna inválido" in e.mensaje for e in errores))

    # ---------- symlinks ----------

    @unittest.skipUnless(tiene_symlinks(), "SO sin soporte de symlinks")
    def test_symlink_en_area(self) -> None:
        añadir_area(self.content, "c", "C1")
        # Crea C2 como symlink a C1
        destino = self.content / "c" / "C2"
        self.assertTrue(crear_symlink(self.content / "c" / "C1", destino))
        errores = validar(self.content)
        self.assertTrue(any("symlink" in e.mensaje.lower() for e in errores))

    @unittest.skipUnless(tiene_symlinks(), "SO sin soporte de symlinks")
    def test_symlink_en_pagina(self) -> None:
        añadir_area(self.content, "c", "C1")
        añadir_pagina(self.content, "c", "C1", "C1-01")
        destino = self.content / "c" / "C1" / "C1-02"
        self.assertTrue(crear_symlink(self.content / "c" / "C1" / "C1-01", destino))
        errores = validar(self.content)
        self.assertTrue(any("symlink" in e.mensaje.lower() for e in errores))

    @unittest.skipUnless(tiene_symlinks(), "SO sin soporte de symlinks")
    def test_symlink_en_media_foto(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["media"] = {"fotos": [{"ruta": "media/foto.png"}]}
        pag = añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        (pag / "media").mkdir()
        # El archivo foto.png es symlink a un archivo externo
        externo = self.tmp / "externo.png"
        externo.write_bytes(b"\x89PNG\r\n\x1a\n")
        self.assertTrue(crear_symlink(externo, pag / "media" / "foto.png"))
        errores = validar(self.content)
        self.assertTrue(any("media.fotos" in e.campo for e in errores))

    @unittest.skipUnless(tiene_symlinks(), "SO sin soporte de symlinks")
    def test_symlink_apunta_fuera_de_content(self) -> None:
        añadir_area(self.content, "c", "C1")
        externo = self.tmp / "externo_area"
        externo.mkdir()
        self.assertTrue(crear_symlink(externo, self.content / "c" / "C2"))
        errores = validar(self.content)
        self.assertTrue(any("symlink" in e.mensaje.lower() for e in errores))

    @unittest.skipUnless(tiene_symlinks(), "SO sin soporte de symlinks")
    def test_symlink_en_carpeta_intermedia_foto(self) -> None:
        añadir_area(self.content, "c", "C1")
        meta = meta_ok("C1-01", "C", "C1")
        meta["media"] = {"fotos": [{"ruta": "media/sub/foto.png"}]}
        pag = añadir_pagina(self.content, "c", "C1", "C1-01", meta=meta)
        externo = self.tmp / "externo_media"
        externo.mkdir()
        (externo / "foto.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        # media es symlink a externo
        self.assertTrue(crear_symlink(externo, pag / "media"))
        errores = validar(self.content)
        self.assertTrue(any("media.fotos" in e.campo for e in errores))


if __name__ == "__main__":
    unittest.main()
