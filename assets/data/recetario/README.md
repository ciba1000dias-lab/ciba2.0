# Catálogo del recetario CIBA

Archivo principal: `assets/data/recetario/recetas.json`.

## Estado del catálogo

**150 números registrados**

- **147 fichas publicables** con ingredientes vinculados, preparación, adaptación por etapa, alérgenos, alertas, conservación y referencias.
- **2 fichas bloqueadas:** n.º 30 y 83, ambas con hígado. No se habilitan hasta evaluar la vitamina A preformada y establecer cantidad y frecuencia seguras.
- **1 número retirado:** n.º 69, duplicaba la combinación de mango y fruta bomba de la n.º 61. Se conserva como registro de trazabilidad, no aparece en resultados.
- La numeración del 1 al 150 está completa y es estable mediante `numero_catalogo`; la interfaz puede ordenar por ese campo sin depender del orden alfabético de los identificadores.

Las preparaciones basadas en ideas de listas externas se han redactado como **versiones editoriales CIBA adaptadas al contexto cubano**, no como transcripciones literales ni como recetas avaladas individualmente por las instituciones citadas. Las fuentes sostienen criterios generales de alimentación complementaria, textura e inocuidad.

## Reglas de publicación

- El motor solo recomienda registros con `publicable: true` y `estado: "aprobada"`.
- La edad mínima se comprueba en meses; la textura se adapta a la etapa y a las habilidades reales.
- Todos los ingredientes obligatorios deben estar identificados y presentes.
- Las restricciones y alergias excluyen coincidencias incompatibles; la lectura de etiquetas y la prevención del contacto cruzado siguen siendo necesarias.
- No se añaden sal, cubitos concentrados, azúcar ni miel antes de los 12 meses.
- Los pescados se especifican por especie y requieren retirar todas las espinas.
- Carnes y huevos deben cocinarse completamente. El pollo/pavo debe alcanzar 74 °C (165 °F); la carne molida de res, 71 °C (160 °F).
- La leche materna extraída se añade después de cocinar y nunca se hierve.
- Las preparaciones para BLW se ofrecen solo con postura, supervisión y forma/textura adecuadas a las habilidades; BLW no significa ofrecer piezas duras o redondas.

## Optimización del recurso

- Un único catálogo JSON; las fuentes institucionales se declaran una sola vez y las recetas las referencian por ID.
- Identificadores estables de alimento y receta, con numeración editorial explícita.
- Separación entre registros publicables y bloqueados; el buscador no expone los bloqueados.
- La IA interpreta los ingredientes escritos, pero no crea recetas, cambia cantidades ni altera las reglas deterministas.
- La fecha de nacimiento, la edad, las alergias y las restricciones se procesan localmente y no se envían al servicio de interpretación.

## Criterios para dar por concluida esta etapa

1. Las 150 posiciones están registradas y numeradas.
2. Las 147 fichas publicables pasan integridad de ingredientes, fuentes, adaptaciones y estado.
3. Los tres registros no publicables quedan excluidos del buscador con motivo explícito.
4. Las pruebas automáticas, construcción y despliegue de GitHub Pages finalizan correctamente.
5. Se verifica en la web que el buscador muestra recetas por edad, ingredientes y restricciones, sin resultados inventados.

## Fuentes marco

- [OMS: alimentación complementaria 6–23 meses](https://www.who.int/publications/i/item/9789240081864)
- [UNICEF Cuba: Guías alimentarias para niñas y niños hasta 2 años](https://www.unicef.org/cuba/informes/guias-alimentarias-para-ninas-y-ninos-cubanos-hasta-2-anos-de-edad)
- [CDC: introducción de alimentos](https://www.cdc.gov/infant-toddler-nutrition/foods-and-drinks/when-what-and-how-to-introduce-solid-foods.html)
- [CDC: riesgos de atragantamiento](https://www.cdc.gov/infant-toddler-nutrition/foods-and-drinks/choking-hazards.html)
- [CDC: pollo e inocuidad](https://www.cdc.gov/food-safety/foods/chicken.html)
