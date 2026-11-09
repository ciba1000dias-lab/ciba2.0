"""Pruebas de integridad y bloqueo seguro del catálogo del recetario CIBA."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "data"


class TestRecetario(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalogo = json.loads((DATA / "recetario" / "recetas.json").read_text(encoding="utf-8"))
        cls.indice = json.loads((DATA / "alimentos-busqueda.json").read_text(encoding="utf-8"))
        cls.alimentos = {a["id"] for a in cls.indice["alimentos"]}
        cls.fuentes = {f["id"] for f in cls.catalogo["fuentes"]}
        cls.fuentes_externas = json.loads((DATA / "recetario" / "fuentes-externas.json").read_text(encoding="utf-8"))

    def test_ids_de_receta_unicos(self) -> None:
        ids = [r["id"] for r in self.catalogo["recetas"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_todos_los_ingredientes_existen_en_biblioteca(self) -> None:
        desconocidos = {
            ingrediente["alimento_id"]
            for receta in self.catalogo["recetas"]
            for ingrediente in receta["ingredientes"]
            if ingrediente["alimento_id"] not in self.alimentos
        }
        self.assertEqual(desconocidos, set())

    def test_todas_las_recetas_tienen_adaptacion_por_etapa(self) -> None:
        etapas = {"6-8", "9-11", "12-23", "24-59"}
        for receta in self.catalogo["recetas"]:
            self.assertTrue(etapas.issubset(receta["adaptacion_por_edad"].keys()), receta["id"])
            self.assertEqual(receta["edad_minima_meses"], 6, receta["id"])
            self.assertEqual(receta["edad_maxima_meses"], 59, receta["id"])

    def test_variedades_de_platano_se_mantienen_diferenciadas(self) -> None:
        por_id = {a["id"]: a for a in self.indice["alimentos"]}
        self.assertIn("platano-fruta", por_id)
        self.assertIn("platano-vianda", por_id)
        self.assertNotEqual(por_id["platano-fruta"]["nombre"], por_id["platano-vianda"]["nombre"])
        self.assertIn("banana", por_id["platano-fruta"]["nombres_alternativos"])
        self.assertIn("plátano verde", por_id["platano-vianda"]["nombres_alternativos"])

    def test_todas_las_fuentes_estan_declaradas(self) -> None:
        for receta in self.catalogo["recetas"]:
            self.assertTrue(receta["fuentes"], receta["id"])
            self.assertTrue(set(receta["fuentes"]).issubset(self.fuentes), receta["id"])

    def test_una_receta_no_se_publica_sin_estado_aprobado(self) -> None:
        for receta in self.catalogo["recetas"]:
            if receta.get("publicable") is True:
                self.assertEqual(receta.get("estado"), "aprobada", receta["id"])
                self.assertEqual(receta.get("revision", {}).get("estado"), "aprobada", receta["id"])

    def test_catalogo_conserva_bloqueo_global(self) -> None:
        if self.catalogo.get("estado_catalogo") != "publicado":
            self.assertFalse(any(r.get("publicable") is True for r in self.catalogo["recetas"]))


    def test_fuentes_externas_tienen_enlaces_y_no_se_habilitan_sin_revision(self) -> None:
        colecciones = self.fuentes_externas["colecciones"]
        self.assertEqual(len({f["id"] for f in colecciones}), len(colecciones))
        for fuente in colecciones:
            self.assertTrue(fuente["url"].startswith("https://"), fuente["id"])
            if fuente.get("entradas_publicadas") is not None:
                self.assertGreater(fuente["entradas_publicadas"], 0, fuente["id"])
            if fuente.get("entradas_publicadas_minimo") is not None:
                self.assertGreaterEqual(fuente["entradas_publicadas_minimo"], 1, fuente["id"])
            self.assertFalse(fuente["recomendacion_automatica"], fuente["id"])

    def test_fuentes_generales_suman_151_entradas_documentadas(self) -> None:
        colecciones = self.fuentes_externas["colecciones"]
        generales = [f for f in colecciones if f["id"] in {
            "nhs-best-start-97", "unicef-venezuela-2026", "first-steps-2023"
        }]
        self.assertEqual(sum(f["entradas_publicadas"] for f in generales), 151)
        self.assertEqual(sum(f.get("entradas_publicadas_minimo", 0) for f in colecciones), 101)

    def test_fuentes_clinicas_se_mantienen_separadas(self) -> None:
        colecciones = {f["id"]: f for f in self.fuentes_externas["colecciones"]}
        for key in ("uhs-babies-specialist", "uhs-toddlers-specialist"):
            self.assertFalse(colecciones[key]["recomendacion_automatica"])
            self.assertIn("especializ", colecciones[key]["uso_ciba"].lower())

    def test_fuentes_historicas_y_periodisticas_no_se_recomiendan_solas(self) -> None:
        colecciones = {f["id"]: f for f in self.fuentes_externas["colecciones"]}
        for key in ("cubahora-cocina-cuba-ninos", "guije-comidas-ninos-historico"):
            self.assertFalse(colecciones[key]["recomendacion_automatica"])
        self.assertIn("históric", colecciones["guije-comidas-ninos-historico"]["alcance"].lower())


if __name__ == "__main__":
    unittest.main()
