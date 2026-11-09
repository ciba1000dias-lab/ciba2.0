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
