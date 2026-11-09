# Catálogo piloto del recetario CIBA

Archivo de datos: `recetas.json`.

## Estado

Este es un piloto de cinco preparaciones de cocina doméstica cubana. Todos los registros permanecen con:

- `publicable: false`
- `estado: revision_especializada_pendiente`

Por tanto, **ninguna receta debe aparecer en resultados de usuarios ni ser recomendada por la IA** hasta completar revisión especializada, editorial y de seguridad.

## Diseño

- Cada ingrediente usa el `id` estable de la biblioteca CIBA.
- Las edades se expresan en meses y tramos.
- Cada receta tiene adaptación de textura por tramo, advertencias, condiciones para combinar ingredientes y fuentes.
- Las referencias se almacenan una sola vez en el catálogo y cada receta las referencia por ID.
- La IA no escribe recetas ni modifica ingredientes, cantidades o instrucciones.

## Revisión pendiente

Un profesional cualificado en nutrición pediátrica debe revisar la pertinencia de ingredientes, cantidades, edades, textura y recomendaciones. El equipo editorial debe revisar la claridad y aplicabilidad en el contexto cubano. También se deben verificar los enlaces y probar las reglas automatizadas antes de habilitar cualquier receta.

Las fuentes citadas sustentan recomendaciones generales de alimentación complementaria y seguridad, no certifican cada receta individual ni sus cantidades.
