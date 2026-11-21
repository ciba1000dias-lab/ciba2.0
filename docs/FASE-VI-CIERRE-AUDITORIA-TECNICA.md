# Fase VI · Cierre de auditoría técnica

Fecha: 21 de noviembre de 2026  
Repositorio: `ciba1000dias-lab/ciba2.0`  
Rama de referencia: `main`

## Resultado ejecutivo

La auditoría automatizada del artefacto de publicación terminó con **0 incidencias en 336 páginas HTML y 3179 enlaces locales revisados**. Se identificaron 1417 enlaces externos, que el auditor registra pero no consulta. La ejecución de integración continua del commit `5fb76ef92474116ba9e394cd321c6e083207a1b5` terminó correctamente: 108 pruebas aprobadas, validación editorial, generación del sitio, comprobaciones de recursos y publicación de GitHub Pages.

## VI-D · Despliegue público

- Commit publicado: `5fb76ef92474116ba9e394cd321c6e083207a1b5`.
- Ejecución: [GitHub Actions #44849712659](https://github.com/ciba1000dias-lab/ciba2.0/actions/runs/44849712659).
- Trabajo `build`: correcto.
- Trabajo `deploy`: correcto.
- Paso `Publicar sitio`: correcto.
- La corrección del encabezado de C1-31 está incluida en el commit publicado.

## VI-E · Navegación y enlaces

- Auditoría del sitio generado: 336 páginas HTML.
- Enlaces locales comprobados: 3179.
- Incidencias: **0**.
- Enlaces externos omitidos por el auditor: 1417; su disponibilidad remota no queda certificada por esta prueba.
- El conjunto de pruebas valida rutas relativas, directorios, fragmentos, rutas de GitHub Pages, páginas anidadas y conservación de cabeceras editoriales.
- El menú global y el Oráculo se incorporan mediante `ciba-global.js` y `ciba-global.css`; el constructor integra el módulo global en las páginas generadas.
- La prueba de ejecución en navegador y la interacción táctil real no forman parte de la integración continua disponible.

### Mejora permanente

La auditoría de enlaces pasa a ejecutarse en modo estricto (`--strict`). Desde este cambio, cualquier enlace local roto impedirá que una nueva versión supere el trabajo de construcción y llegue al despliegue.

## VI-F · Presentación y adaptación móvil

Comprobaciones estáticas verificadas en el repositorio y en CI:

- Pruebas de preservación de las cabeceras editoriales.
- Prueba de identidad visual de las cuatro columnas y de la paleta azul de INFORMÁTICA.
- Reglas responsive para anchos de 600, 480 y 380 píxeles en el sistema global.
- Controles globales con estados accesibles y reglas para movimiento reducido.
- Pruebas de generación y normalización idempotente del sistema editorial.

**Límite de verificación:** no se ejecutó una inspección visual real en navegador ni una prueba táctil en un teléfono físico. Las pruebas estáticas y el build no permiten certificar ausencia absoluta de solapamientos o diferencias de renderizado entre navegadores. Este límite queda explícito y no se presenta como una prueba realizada.

## VI-G · Recursos y multimedia

La ejecución de CI completó correctamente:

- Validación de contenidos y medios declarados.
- Construcción del catálogo y copia de medios permitidos.
- Preparación/optimización de imágenes de la biblioteca.
- Verificación de la firma, tamaño y SHA-256 del tríptico de vacunación incorporado al artefacto.
- Verificación del audio maestro C7-04.
- Restauración de la caché de los podcasts C4-10, C4-11 y C4-12.
- Generación de la cartilla de vacunación PDF A4 desde el SVG aprobado.

La validación acredita integridad de los recursos comprobados por el pipeline; no sustituye la revisión editorial individual de cada fotografía, video o recurso externo.

## Pruebas globales

- **108 pruebas automatizadas: aprobadas.**
- Sintaxis de JavaScript: aprobada.
- Validación editorial: aprobada.
- Construcción del sitio: aprobada.
- Auditoría interna del artefacto: 0 incidencias.
- Publicación de GitHub Pages: aprobada.

## Criterio de cierre

Quedan cerradas las tareas técnicas automatizables de VI-D, VI-E y VI-G, así como las comprobaciones estáticas y responsive de VI-F. La única comprobación que no puede certificarse desde este entorno es la inspección visual/táctil en dispositivos reales. No se modifica contenido clínico en esta fase.

La Fase VI queda documentada como **cierre técnico automatizado**, con la limitación de prueba física indicada y con el control estricto de enlaces incorporado para los despliegues futuros.
