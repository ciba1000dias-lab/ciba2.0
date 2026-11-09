# Catálogo piloto del recetario CIBA

Archivo de datos: `recetas.json`.

## Estado actual

El catálogo operativo contiene **15 fichas completas** de preparaciones de cocina doméstica cubana. Las 15 fueron aprobadas expresamente por el especialista responsable del recetario en la revisión del 9 de noviembre de 2026 y tienen:

- `publicable: true`
- `estado: aprobada`
- `revision.estado: aprobada`

Esta habilitación corresponde a las 15 fichas estructuradas que existen actualmente en `recetas.json`. Las otras preparaciones aceptadas en la planificación conversacional todavía no están incorporadas como fichas completas y no aparecerán en resultados hasta que tengan ingredientes vinculados, cantidades, preparación, adaptación por edad, alertas, fuentes y registro de aprobación. El catálogo permanece abierto a ampliaciones.

## Motor de selección

El archivo `assets/js/ciba-recetario-motor.js` aplica reglas deterministas:

- Solo acepta recetas con `publicable: true` y `estado: aprobada`.
- Comprueba el rango de edad y la adaptación de textura correspondiente: 6–8, 9–11, 12–23 y 24–59 meses.
- Exige que estén presentes todos los ingredientes obligatorios reconocidos.
- Excluye recetas según el alérgeno específico identificado en el campo local de restricciones.
- Aplica el filtro vegetariano y bloquea solicitudes con restricciones clínicas no especificadas.
- No envía edad, alergias ni restricciones al servicio de IA. La IA solo interpreta el texto de ingredientes.

La identificación automática de alérgenos es conservadora y limitada a los alimentos y términos expresamente mapeados. No sustituye la lectura de etiquetas, la prevención del contacto cruzado ni un plan individual indicado por alergología/nutrición. Si la alergia o restricción no se puede identificar con claridad, el sistema no ofrece recetas.

## Diseño de datos

- Cada ingrediente usa el `id` estable de la biblioteca CIBA.
- Las edades se expresan en meses y tramos.
- Cada receta contiene adaptación de textura, advertencias, condiciones para combinar ingredientes y fuentes.
- Las referencias se almacenan una sola vez en el catálogo y cada receta las referencia por ID.
- La IA no escribe recetas ni modifica ingredientes, cantidades o instrucciones.

## Alcance de la aprobación

La aprobación registrada corresponde a las fichas actuales y a la valoración del especialista responsable del proyecto. No constituye una certificación externa ni sustituye la actualización periódica de fuentes, la comprobación de enlaces o la reevaluación si cambia una receta. Las fuentes citadas sustentan recomendaciones generales de alimentación complementaria y seguridad, no certifican por sí solas cada receta ni sus cantidades.


## Prototipo funcional

La interfaz normal muestra únicamente registros aprobados. Después de reconocer los ingredientes, solicita confirmación y devuelve las recetas cuyos ingredientes obligatorios están todos presentes, filtradas por edad y restricciones. Si hay términos sin identificar, espera a que se aclaren; si no existe coincidencia, lo comunica sin inventar una receta ni añadir ingredientes. El modo `?demo=1` queda reservado para borradores futuros y no es necesario para el piloto operativo actual. Las nuevas recetas se incorporan como registros independientes siguiendo este mismo esquema; el motor no requiere reescritura.
