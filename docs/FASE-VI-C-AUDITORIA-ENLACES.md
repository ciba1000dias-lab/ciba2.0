# Fase VI-C · Auditoría inicial de enlaces internos

Fecha: 20 de noviembre de 2026  
Base: compilación de la rama `fase-vi-c/auditoria-enlaces-2026-11-20`, con la normalización de migas de la Fase VI-B.

## Resultado de la primera ejecución

| Indicador | Resultado |
|---|---:|
| Páginas HTML examinadas | 334 |
| Enlaces locales revisados | 3 162 |
| Enlaces externos omitidos | 1 401 |
| Incidencias locales detectadas | 50 |

La auditoría se ejecutó sobre `dist`, es decir, sobre el artefacto construido que se publica, no solamente sobre los archivos fuente. Los enlaces externos no se consultaron ni se calificaron como correctos o incorrectos.

## Evolución de la línea base

| Hito | Incidencias detectadas |
|---|---:|
| Auditoría inicial | 50 |
| Tras corregir las rutas del módulo global | 38 |
| Tras corregir rutas editoriales, recursos y publicación de artículos anidados | 1 |

La reducción se verificó en ejecuciones de CI sobre el artefacto construido. La única incidencia que permanece es `c/C1/lactancia/index.html` → `../C1-31/`: el índice de lactancia declara ese artículo como publicado, pero no existe `content/c/C1/C1-31/` en el repositorio. Se deja sin redirección automática porque no hay un artículo equivalente al que enviar a las familias. Su resolución requiere recuperar o redactar y aprobar el contenido C1-31.

## Tipos de incidencias observadas

El primer informe detectó, entre otros:

- Rutas hacia áreas o subsecciones que no se encuentran en el destino esperado.
- Referencias a páginas auxiliares alojadas en `_paginas/` que no aparecen en la misma ruta del artefacto.
- Referencias a recursos multimedia que no se encuentran junto al artículo.
- Rutas relativas al módulo global JavaScript que parecen exceder o no alcanzar la raíz del sitio en algunas páginas profundas.
- Fragmentos internos (`#id`) que no se encuentran en el documento de origen o destino.

**Importante:** las 50 incidencias son hallazgos automáticos iniciales, no 50 errores confirmados de la web pública. Antes de modificar enlaces se debe clasificar cada caso como error real, ruta intencional, recurso generado dinámicamente o falso positivo del auditor. No se deben crear páginas o identificadores ficticios para silenciar la herramienta.

## Instrumentación añadida

- `scripts/audit_internal_links.py`: analiza enlaces `href`, `src`, `poster` y `action`; comprueba destinos locales, directorios, fragmentos HTML y que las rutas permanezcan dentro del sitio.
- `tests/test_internal_links.py`: prueba rutas relativas, directorios, archivos inexistentes, fragmentos y URL base de GitHub Pages.
- El workflow ejecuta el análisis en modo diagnóstico no bloqueante y guarda el JSON temporal fuera del sitio publicado.

## Siguiente trabajo

1. Clasificar las 50 incidencias por origen, destino y tipo.
2. Corregir rutas reales sin alterar contenidos clínicos ni jerarquías editoriales.
3. Mejorar el auditor para distinguir recursos dinámicos, atributos duplicados y rutas válidas de GitHub Pages.
4. Añadir un umbral estricto cuando el inventario heredado esté saneado.
5. Repetir la auditoría en el artefacto final y comparar el número de incidencias.

Esta fase no certifica todavía que todos los enlaces estén correctos. Establece una línea base reproducible para corregirlos con control.
