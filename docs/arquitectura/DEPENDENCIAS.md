# CIBA · Registro de dependencias

> Registro inicial. Fecha: 27 de noviembre de 2026.

## Dependencias de producción incorporadas por esta propuesta

**Ninguna.** La portada alternativa no añade paquetes, CDN ni solicitudes a terceros. Reutiliza los archivos locales y el sistema global de CIBA que ya existen en el repositorio.

## Herramientas ya existentes en el proyecto

| Recurso | Uso actual | Observación |
|---|---|---|
| HTML, CSS y JavaScript nativos | Interfaz y comportamiento | Mantener como base |
| `assets/js/ciba-global.js` | Menú, buscador global, navegación y preferencias | Reutilizado por la portada alternativa |
| `assets/css/ciba-global.css` | Estilos compartidos de navegación y componentes | Cargado por el módulo global |
| `data/catalogo.json` | Catálogo generado de páginas publicadas | Fuente del bloque de lecturas recientes y del buscador |
| `assets/data/alimentos-busqueda.json` | Índice de búsqueda de alimentos | Utilizado por el buscador global |
| `assets/images/*.webp` | Imágenes locales | No se cargan desde CDN |

## Candidatos, todavía no instalados

| Biblioteca | Licencia declarada en GitHub | Decisión |
|---|---|---|
| Pagefind | MIT | Primera candidata para una prueba de búsqueda de texto completo |
| Workbox | MIT | Posponer hasta inventariar y probar la estrategia PWA/Service Worker |
| Fuse.js | Apache-2.0 | Alternativa ligera para catálogos pequeños; comparar con Pagefind |
| axe-core | MPL-2.0 | Añadir como control de calidad en pruebas |
| Lighthouse | Apache-2.0 | Utilizar como auditoría de CI o revisión periódica |
| SortableJS | MIT | Sin necesidad funcional inmediata |

## Reglas

- No instalar bibliotecas mediante CDN en producción.
- No añadir dependencias solo por estética.
- No marcar un candidato como instalado hasta que el archivo esté en el repositorio y exista una prueba.
- Registrar la versión exacta y el texto de licencia correspondiente.
- Revisar los requisitos de atribución, avisos y redistribución de cada licencia.
- Cualquier dependencia nueva debe pasar una prueba de carga en Android y una auditoría de enlaces internos.

## Nota sobre Pagefind

La búsqueda actual de CIBA ya consulta el catálogo editorial y el índice de alimentos desde `ciba-global.js`. Pagefind puede ampliar la búsqueda al texto completo de los artículos, pero requiere una fase de construcción del índice. No se conecta todavía a la portada alternativa para evitar duplicar buscadores o alterar el comportamiento existente sin una comparación funcional.
