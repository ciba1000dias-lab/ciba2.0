import test from "node:test";
import assert from "node:assert/strict";
import {
  validarEntrada,
  extraerJSON,
  validarResultado
} from "./index.js";

const candidates = [
  { id: "platano-fruta", name: "Plátano fruta", aliases: ["banana", "guineo"] },
  { id: "arroz", name: "Arroz", aliases: [] }
];

test("acepta ingredientes y candidatos válidos", () => {
  const result = validarEntrada({
    ingredients: "arroz, guineo y zanahoria",
    candidates
  });
  assert.equal(result.ok, true);
  assert.equal(result.value.candidates.length, 2);
});

test("rechaza texto excesivo", () => {
  const result = validarEntrada({
    ingredients: "a".repeat(501),
    candidates
  });
  assert.equal(result.ok, false);
});

test("rechaza IDs con formato inválido", () => {
  const result = validarEntrada({
    ingredients: "arroz",
    candidates: [{ id: "../secreto", name: "Arroz" }]
  });
  assert.equal(result.ok, false);
});

test("extrae JSON incluso si el modelo añade delimitadores", () => {
  const result = extraerJSON('Resultado:\n```json\n{"recognizedIds":["arroz"],"unknownTerms":[]}\n```');
  assert.deepEqual(result, {
    recognizedIds: ["arroz"],
    unknownTerms: []
  });
});

test("descarta IDs inventados por el modelo", () => {
  const result = validarResultado({
    recognizedIds: ["arroz", "leche-inventada", "arroz"],
    unknownTerms: ["algo desconocido"],
    clarification: ""
  }, candidates);

  assert.deepEqual(result.recognizedFoods, [
    { id: "arroz", name: "Arroz" }
  ]);
  assert.deepEqual(result.unknownTerms, ["algo desconocido"]);
  assert.equal(result.requiresConfirmation, true);
});

test("rechaza una salida sin estructura reconocible", () => {
  assert.equal(validarResultado({ texto: "arroz" }, candidates), null);
});


import { readFileSync } from "node:fs";

const recipeCatalog = JSON.parse(
  readFileSync(new URL("../../assets/data/recetario/recetas.json", import.meta.url), "utf8")
);

const foodGroups = [
  "frutas", "viandas", "vegetales", "legumbres", "cereales",
  "carnes", "pescados", "leches", "yogures", "huevos-quesos"
];

const foodIds = new Set();
for (const group of foodGroups) {
  const data = JSON.parse(
    readFileSync(new URL(`../../assets/data/alimentos/${group}.json`, import.meta.url), "utf8")
  );
  for (const food of data.alimentos) foodIds.add(food.id);
}

test("el catálogo piloto contiene recetas y fuentes identificadas", () => {
  assert.ok(recipeCatalog.recetas.length >= 1);
  assert.ok(recipeCatalog.fuentes.length >= 1);
  assert.equal(new Set(recipeCatalog.recetas.map(recipe => recipe.id)).size, recipeCatalog.recetas.length);
});

test("todos los ingredientes de recetas existen en la biblioteca CIBA", () => {
  for (const recipe of recipeCatalog.recetas) {
    for (const ingredient of recipe.ingredientes) {
      assert.ok(foodIds.has(ingredient.alimento_id), `${recipe.id}: alimento inexistente ${ingredient.alimento_id}`);
    }
  }
});

test("ninguna receta piloto se habilita sin revisión especializada", () => {
  for (const recipe of recipeCatalog.recetas) {
    assert.equal(recipe.publicable, false, recipe.id);
    assert.equal(recipe.estado, "revision_especializada_pendiente", recipe.id);
  }
});

test("todas las referencias declaradas resuelven a una fuente del catálogo", () => {
  const sourceIds = new Set(recipeCatalog.fuentes.map(source => source.id));
  for (const recipe of recipeCatalog.recetas) {
    for (const sourceId of recipe.fuentes) {
      assert.ok(sourceIds.has(sourceId), `${recipe.id}: fuente inexistente ${sourceId}`);
    }
  }
});


test("rechaza alimentos que no pertenecen a la biblioteca oficial", () => {
  const result = validarEntrada({
    ingredients: "algo",
    candidates: [{ id: "alimento-inventado", name: "Alimento inventado" }]
  });
  assert.equal(result.ok, false);
});

test("no permite cambiar el nombre oficial de un ID válido", () => {
  const result = validarEntrada({
    ingredients: "calabaza",
    candidates: [{ id: "calabaza", name: "Chocolate" }]
  });
  assert.equal(result.ok, false);
});

test("usa los sinónimos oficiales y no los enviados por el navegador", () => {
  const result = validarEntrada({
    ingredients: "guineo",
    candidates: [{ id: "platano-fruta", name: "Plátano fruta", aliases: ["nombre-falso"] }]
  });
  assert.equal(result.ok, true);
  assert.ok(result.value.candidates[0].aliases.includes("banana"));
  assert.ok(!result.value.candidates[0].aliases.includes("nombre-falso"));
});
