# CIBA · Especificación inicial del recetario interactivo

**Nombre de trabajo:** ¿Qué cocino hoy?  
**Ubicación editorial:** Crianza → Alimentación y lactancia (C1).  
**Estado:** Diseño funcional aprobado para desarrollo por etapas.  
**Principio:** sugerencias culinarias educativas, basadas en un catálogo curado; nunca diagnóstico, prescripción ni generación improvisada de recetas.

## 1. Propósito

Ayudar a madres, padres y cuidadores a encontrar preparaciones sencillas a partir de los alimentos que tienen en casa, adaptadas a la edad y etapa del niño, con instrucciones comprensibles, advertencias de seguridad y referencias sanitarias verificables.

El recurso debe ser especialmente útil en el contexto cubano, sin asumir que todas las familias disponen de los mismos alimentos, equipos o condiciones de refrigeración.

## 2. Experiencia del usuario

1. **Edad:** el usuario puede introducir fecha de nacimiento o edad manual. La fecha se calcula en el navegador con la fecha local del día, sin pedir datos personales a un servidor. Mostrar edad en años y meses cuando corresponda. Rechazar fechas futuras y edades incoherentes.
2. **Ingredientes:** campo de texto libre. Aceptar frases naturales, listas, comas, puntos, errores ortográficos frecuentes, tildes omitidas, singular/plural y sinónimos regionales. Ejemplo: «Tengo arroz, zanahoria, pollo y un poquito de aceite».
3. **Alergias y restricciones:** preguntar por alergias conocidas y restricciones relevantes antes de buscar recetas. La ausencia de respuesta no se interpreta como ausencia de alergias.
4. **Resultado:** presentar solo recetas del catálogo que superen las reglas de edad, ingredientes y seguridad. Indicar qué ingredientes del usuario se utilizaron y cuáles no.
5. **Sin coincidencias seguras:** explicar por qué no se recomienda una receta con esos ingredientes y, si procede, qué ingrediente adicional seguro podría completar una preparación. No inventar sustituciones ni forzar resultados.

## 3. Tramos de edad

El catálogo debe clasificar explícitamente cada receta. Tramos iniciales propuestos:

- Menores de 6 meses: no generar recetas de alimentación complementaria; explicar que la alimentación complementaria no se recomienda de forma general antes de alrededor de los 6 meses.
- 6–8 meses.
- 9–11 meses.
- 12–23 meses.
- 24–59 meses.

La edad por sí sola no garantiza que el niño esté preparado. La interfaz debe recordar las señales de preparación y las situaciones que requieren valoración profesional. Prematuridad, dificultades de deglución, alergias diagnosticadas, enfermedades, dietas terapéuticas o problemas de crecimiento deben activar un aviso y evitar recomendaciones personalizadas automáticas.

## 4. Reconocimiento de ingredientes

- Reutilizar el índice de alimentos existente: `assets/data/alimentos-busqueda.json` y las fichas de `assets/data/alimentos/*.json`.
- Normalizar Unicode, tildes, mayúsculas, puntuación, espacios, plurales y variantes comunes.
- Mantener un diccionario editorial explícito de sinónimos cubanos y regionales.
- Corregir solo errores frecuentes y de alta confianza. Si hay ambigüedad (por ejemplo, nombres que pueden referirse a alimentos distintos), pedir aclaración en vez de adivinar.
- Mostrar ingredientes reconocidos y no reconocidos para que el usuario pueda corregirlos.
- No enviar el texto escrito a terceros ni almacenarlo en un servidor en la primera versión.

## 5. Motor de recetas: catálogo curado, no improvisación

La primera versión debe funcionar sin servicios externos, sin claves API y sin costes recurrentes. GitHub Pages es un alojamiento estático: no puede ocultar claves privadas ni ejecutar un modelo generativo de forma segura en el servidor.

Por tanto, las recetas se escribirán y revisarán editorialmente en archivos de datos locales. El motor solo podrá seleccionar y adaptar recetas aprobadas mediante reglas explícitas. No podrá inventar cantidades, tiempos, ingredientes, sustituciones ni instrucciones.

Cada receta deberá contener como mínimo:

- identificador, título y descripción;
- tramos de edad autorizados;
- ingredientes, cantidades orientativas y sustituciones permitidas (si están validadas);
- pasos numerados y métodos de cocción;
- textura y forma de ofrecer según la etapa;
- rendimiento orientativo, cuando pueda establecerse;
- alérgenos y advertencias;
- alimentos o ingredientes incompatibles;
- conservación y recalentamiento, solo cuando existan indicaciones verificadas;
- fuentes bibliográficas con institución, título, URL y fecha de consulta/revisión;
- fecha y estado de revisión editorial.

No presentar una receta como nutricionalmente completa ni afirmar que cubre necesidades diarias.

## 6. Reglas de seguridad obligatorias

Antes de mostrar una receta, comprobar al menos:

- edad compatible y etapa de desarrollo;
- miel: nunca antes de los 12 meses;
- ausencia de sal y azúcares añadidos como recomendación para lactantes; evitar productos con alto contenido de sodio o azúcar;
- leche de vaca como bebida: no antes de los 12 meses, salvo indicación clínica; distinguir su uso culinario cuando proceda y esté validado;
- leche cruda, huevos/carnes/pescados crudos o insuficientemente cocidos y lácteos no pasteurizados;
- pescados con mercurio elevado y recomendaciones vigentes sobre selección y frecuencia;
- frutos secos enteros, uvas enteras, salchichas en rodajas, trozos duros/redondos y otros riesgos de atragantamiento;
- semillas, espinas, huesos, cáscaras duras y partes no comestibles;
- cocción segura, higiene y contaminación cruzada;
- alergias conocidas y alérgenos presentes;
- ingredientes no reconocidos o ambiguos.

Las reglas deben estar centralizadas y ser comprobables mediante pruebas automatizadas. Una receta con una incompatibilidad crítica se bloquea; no basta con añadir una advertencia al pie.

## 7. Presentación de cada receta

1. Nombre y tramo de edad compatible.
2. Por qué coincide con los ingredientes introducidos.
3. Ingredientes utilizados y cantidades orientativas.
4. Preparación paso a paso.
5. Textura y forma segura de servir.
6. Advertencias concretas y alérgenos.
7. Conservación, solo si está respaldada.
8. Referencias verificables con símbolo °.
9. Aviso educativo y recomendación de consultar a un profesional cuando existan circunstancias particulares.

## 8. Aviso de alcance y responsabilidad

Texto de trabajo, pendiente de revisión jurídica antes de publicar:

> Este recetario es una herramienta educativa de orientación culinaria. Sus propuestas no constituyen consejo médico, diagnóstico, tratamiento ni prescripción nutricional individualizada. La información se basa en referencias seleccionadas y puede no contemplar las circunstancias particulares de cada niño. La persona adulta responsable debe verificar los ingredientes, alergias, higiene, cocción, textura y forma de ofrecer los alimentos. Ante prematuridad, enfermedades, dificultades para tragar, alergias, problemas de crecimiento o dietas especiales, consulte con un profesional cualificado. CIBA no garantiza resultados ni que una receta sea adecuada para todas las situaciones individuales.

El aviso no sustituye la obligación de diseñar, revisar y probar el recurso con criterios de seguridad. No afirmar que un descargo elimina toda responsabilidad legal.

## 9. Arquitectura técnica propuesta

- Página independiente y responsiva, dentro de C1.
- Datos de recetas separados del HTML y JavaScript.
- Motor de reconocimiento local, con normalización y diccionario de sinónimos.
- Motor de reglas determinista, con prioridad de bloqueos críticos.
- Cálculo de edad en el navegador; no guardar la fecha de nacimiento.
- Sin API de pago, sin claves expuestas y sin envío de ingredientes a terceros.
- Accesible desde el carrusel de recursos destacados de la portada y desde el menú global.
- Integración con el buscador ancestral solo mediante acceso/enlace; no modificar su funcionamiento.

## 10. Etapas de desarrollo

**Etapa 1 — Base segura:** página, cálculo de edad, entrada de ingredientes, reconocimiento con confirmación y catálogo pequeño de recetas revisadas.  
**Etapa 2 — Seguridad y calidad:** filtros por edad, alergias, ingredientes incompatibles, bloqueos, mensajes de no coincidencia y pruebas automatizadas.  
**Etapa 3 — Ampliación:** más recetas cubanas y opciones económicas, variedad de texturas, referencias y pruebas con entradas reales escritas de distintas maneras.  
**Etapa 4 — Integración:** portada, menú global, buscador y analítica respetuosa con la privacidad, solo si se decide incorporar y sin recoger datos sensibles.

## 11. Criterios para considerar lista la primera versión

- El cálculo de edad funciona en fechas límite, años bisiestos y cambios de mes/año.
- No aparecen recetas antes de la edad autorizada.
- Los ingredientes se reconocen sin depender de puntuación, tildes o mayúsculas.
- Las entradas ambiguas o desconocidas no provocan recomendaciones inventadas.
- Los bloqueos críticos impiden mostrar recetas inseguras.
- Cada receta tiene fuentes verificables y fecha de revisión.
- La interfaz funciona en móvil y no altera el buscador ancestral ni la biblioteca.
- Las pruebas y el workflow de publicación terminan correctamente.
