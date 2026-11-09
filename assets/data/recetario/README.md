# Catálogo ampliado del recetario CIBA

Archivo de datos: `recetas.json`.

## Estado actual

El catálogo contiene **35 fichas completas y operativas**: las 15 preparaciones iniciales, diez preparaciones frutales aceptadas sin cambios (51–60), las dos sustituciones aceptadas (61 y 66) y ocho fichas nuevas hasta la 75. La preparación 69 no se publica porque duplica la combinación de la 61. Todas tienen:

- `publicable: true`
- `estado: aprobada`
- `revision.estado: aprobada`

La ampliación se realiza por etapas. Las preparaciones restantes de la lista 1–150 todavía no se incorporan como fichas completas; no deben anunciarse como disponibles hasta completar sus ingredientes vinculados, cantidades, preparación, adaptación por edad, alertas, fuentes y registro de aprobación.

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

## Funcionamiento de la interfaz

La interfaz normal muestra únicamente registros aprobados. Después de reconocer los ingredientes, presenta directamente las preparaciones que coinciden con todos los ingredientes obligatorios, la edad y las restricciones indicadas; no añade una pantalla intermedia de confirmación. Si algún término no se reconoce con suficiente seguridad, solicita aclararlo antes de buscar preparaciones. Si no hay coincidencias, lo comunica sin inventar recetas ni añadir alimentos.

Las aclaraciones breves se muestran mediante controles `°`, que abren mensajes flotantes también en pantallas táctiles. La fecha de nacimiento se utiliza localmente para calcular la edad; la edad, las alergias y las restricciones no se envían al servicio de IA.

El modo `?demo=1` queda reservado para borradores futuros y no es necesario para el piloto operativo actual. Las nuevas recetas se incorporan como registros independientes siguiendo este mismo esquema; el motor no requiere reescritura.
