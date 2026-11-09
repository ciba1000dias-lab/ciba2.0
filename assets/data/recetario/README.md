# Catálogo piloto del recetario CIBA

Archivo de datos: `recetas.json`.

## Estado actual

El catálogo contiene **15 preparaciones originales** de cocina doméstica cubana. Todas permanecen con:

- `publicable: false`
- `estado: revision_especializada_pendiente`

Por tanto, ninguna receta aparece como recomendación hasta completar la revisión especializada, editorial y de seguridad. El catálogo incluye preparaciones de un ingrediente y combinaciones de viandas, cereales, vegetales, legumbres, pollo y huevo.

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

## Revisión pendiente

Un profesional cualificado en nutrición pediátrica debe revisar la pertinencia de ingredientes, cantidades, edades, texturas, combinaciones y recomendaciones. El equipo editorial debe revisar claridad y aplicabilidad en el contexto cubano. También se deben verificar los enlaces, las reglas automatizadas y los riesgos de contaminación cruzada antes de habilitar cualquier receta.

Las fuentes citadas sustentan recomendaciones generales de alimentación complementaria y seguridad, no certifican cada receta individual ni sus cantidades.


## Prototipo funcional

La interfaz normal mantiene el filtro estricto: solo muestra registros con `publicable: true` y `estado: aprobada`. Para presentar el flujo completo con contenido real mientras las 15 preparaciones originales siguen en revisión, existe un modo de demostración activado únicamente con `?demo=1` en la URL del recetario. Este modo selecciona exclusivamente registros no publicables, conserva los filtros deterministas de edad, ingredientes y restricciones, y marca cada tarjeta como **BORRADOR · NO APROBADO**. La advertencia indica que el contenido sirve para demostrar la interacción y no para orientar la alimentación real. Activar el modo demo no cambia el catálogo, no modifica `publicable` y no autoriza recomendaciones. Las nuevas recetas se incorporan como registros independientes siguiendo este mismo esquema; el motor no requiere reescritura.
