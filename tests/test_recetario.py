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


if __name__ == "__main__":
    unittest.main()
