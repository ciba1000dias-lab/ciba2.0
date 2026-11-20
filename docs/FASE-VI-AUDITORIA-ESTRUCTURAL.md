# Fase VI · Auditoría estructural de CIBA
Fecha: 20 de noviembre de 2026  
Base revisada: `main`, después de la Fase V.

## Alcance
Revisión del árbol Git, generador de catálogo, validador, normalizador de migas, módulo global y pruebas. No es una inspección visual en navegador ni una prueba manual en teléfono. No se modificaron contenidos clínicos.

## Inventario verificado
| Elemento | Total |
|---|---:|
| HTML dentro de `content/` | 311 |
| `meta.json` | 243 |
| `area.json` | 38 |
| Páginas auxiliares dentro de `_paginas/` | 51 |

El recuento previo de 312 HTML se corrige a 311.

| Columna | HTML | meta.json | area.json |
|---|---:|---:|---:|
| CRIANZA | 171 | 114 | 7 |
| INFORMÁTICA | 78 | 67 | 10 |
| BIENESTAR | 56 | 62 | 11 |
| ACOMPAÑAMIENTO | 6 | 0 | 10 |

BIENESTAR tiene diez áreas principales B1–B10. El undécimo `area.json` corresponde al registro anidado B4/B4-01, no a una undécima área principal. ACOMPAÑAMIENTO dispone de diez registros A1–A10, pero solo A1–A5 tienen HTML fuente propio; A6–A10 dependen de la generación automática a partir de `area.json`.

## Hallazgos

### Migas de pan
- `_normalizar_migas_y_metadatos()` reconoce portada de columna, área, subsección y artículo incluidos en el catálogo.
- Las 51 páginas auxiliares `_paginas/` se publican fuera del catálogo editorial; la función no les asigna una jerarquía de migas.
- Si detecta una clase de breadcrumb/migas existente, conserva el HTML y no reconstruye la ruta. Pueden persistir rutas antiguas.
- La prueba localizada `test_normaliza_migas_y_metadatos_de_articulos` cubre un artículo de CRIANZA y su portada de columna, no todas las columnas ni todos los niveles.

**Conclusión:** la función existe, pero no hay pruebas suficientes para certificar cobertura correcta de todas las páginas.

### Menú global y Oráculo
- El constructor integra `ciba-global.js` en todos los `index.html` del artefacto cuando están presentes el JS y el CSS globales.
- Comprueba estáticamente que cada HTML tenga una sola referencia a la versión vigente del módulo.
- Esto verifica la presencia del script, no el funcionamiento visual, los enlaces ni la ausencia de solapamientos en móviles.
- El módulo mantiene listas de rutas y áreas; deben compararse con el catálogo y verificarse en navegador antes de hacerlas fuente única del gestor.

**Conclusión:** integración de build automatizada; funcionamiento real pendiente de prueba de navegador.

### Modelo editorial
- El repositorio combina HTML individual, `meta.json`, `area.json`, subsecciones modeladas como contenedores archivados y páginas auxiliares fuera del catálogo.
- Hay 86 `index.html` sin `meta.json`; incluyen portadas de columna/área y páginas auxiliares. No deben tratarse como 86 artículos incompletos.
- ACOMPAÑAMIENTO requiere un modelo de metadatos para sus diez áreas y sus contenidos, sin romper las rutas existentes.

**Conclusión:** no conviene instalar un CMS genérico ni migrar todo en bloque. El gestor debe incluir un adaptador para el legado y un modelo estructurado para contenidos nuevos.

## Acciones prioritarias
1. Ampliar pruebas de migas para las cuatro columnas, áreas generadas, subsecciones y artículos anidados.
2. Definir migas explícitas para páginas auxiliares y PLATAFORMA, sin inventar jerarquías.
3. Normalizar el modelo editorial de ACOMPAÑAMIENTO y conservar A1–A10.
4. Validar enlaces internos y destinos en el artefacto generado.
5. Probar menú y Oráculo en todas las profundidades y anchos móviles.
6. Diseñar el esquema del gestor para leer el legado y exportar al generador actual.

## Requisitos para CIBA Gestor Editorial
- Mantener GitHub Pages como sitio público estático y el gestor en un área administrativa separada.
- Adaptador para HTML, `meta.json`, `area.json`, subsecciones y páginas auxiliares.
- Modelo estructurado, vista previa, historial, validación y exportación compatible con `scripts/build_catalog.py`.
- Permisos diferenciados de lectura, edición, aprobación clínica y publicación.
- No guardar tokens personales de GitHub en el navegador; utilizar OAuth o una GitHub App con permisos mínimos.
- Diseñar una interfaz Apps SDK y servidor MCP, pero conservar el modo web independiente.

## Compatibilidad ChatGPT
La documentación actual de OpenAI diferencia Apps SDK y servidores MCP personalizados. El acceso a herramientas MCP de escritura depende del plan y la configuración del espacio de trabajo. El gestor debe poder funcionar independientemente de la disponibilidad de esas funciones en una cuenta concreta.

## Criterios pendientes para cerrar Fase VI
- Pruebas ampliadas de cobertura de migas.
- Validación de enlaces y rutas del artefacto.
- Pruebas funcionales de menú y Oráculo.
- Inspección visual móvil de páginas representativas de cada columna y páginas auxiliares.

Esta auditoría documenta el estado estructural; no declara cerrada la Fase VI hasta completar las comprobaciones anteriores.
