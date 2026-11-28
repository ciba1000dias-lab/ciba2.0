# CIBA · Arquitectura técnica evolutiva

> Documento interno de trabajo. Propuesta inicial: 27 de noviembre de 2026.
> Complementa, no sustituye, `docs/ARQUITECTURA.md` (versión 1.4).

## 1. Arquitectura que existe y debe preservarse

El repositorio ya utiliza una arquitectura estática con separación editorial:

```
content/  →  scripts/  →  dist/
                    ↘ catálogo público
assets/              ↘ interfaz y recursos locales
index.html            ↘ portada
```

- `content/`: fuentes editoriales, metadatos y artículos.
- `scripts/`: validación, construcción, optimización y auditorías.
- `assets/`: estilos, JavaScript, imágenes, datos y multimedia.
- `dist/`: salida generada que se publica en GitHub Pages.
- `data/catalogo.json`: catálogo público generado.
- `.github/workflows/static.yml`: pruebas, validación, construcción y publicación.

La portada actual y el módulo global son funcionales y contienen navegación y buscador propios. La propuesta alternativa reutiliza ese sistema, no lo reemplaza.

## 2. Principios de evolución

1. Mantener HTML/CSS/JavaScript nativos como base.
2. Mobile-first y carga progresiva.
3. No introducir backend ni servicios de pago para funciones que pueden resolverse estáticamente.
4. No duplicar el buscador, el menú ni el catálogo.
5. Mantener recursos locales y tolerancia a conexiones inestables.
6. Mantener identificadores técnicos fuera de la interfaz familiar.
7. No publicar metadatos editoriales privados ni archivos internos.
8. Conservar el build atómico, la allowlist y las pruebas existentes.
9. Toda mejora debe ser reversible y verificable antes de sustituir la portada.
10. No modificar el flujo de despliegue ni activar Workers como parte de esta propuesta.

## 3. Capas funcionales propuestas

### Presentación
HTML semántico, CSS propio, paleta CIBA, SVG locales y componentes accesibles.

### Navegación
Menú global actual de `ciba-global.js`; no se crea un segundo menú.

### Descubrimiento
Buscador global existente como primera capa. Pagefind se evaluará para búsqueda de texto completo en artículos, sin desplazar el buscador de alimentos ni crear resultados duplicados.

### Contenidos
`content/` sigue siendo la fuente editorial. El catálogo público se genera mediante `scripts/build_catalog.py`.

### Disponibilidad
Primero se debe auditar si ya existe registro de Service Worker o manifiesto en el despliegue. El árbol actual consultado no mostró un `sw.js`, manifiesto ni service worker en la raíz. No se instalará Workbox hasta confirmar el comportamiento real de la aplicación publicada y definir una estrategia de caché segura.

### Calidad
- Pruebas Python existentes.
- Comprobación de sintaxis JavaScript.
- Validación editorial.
- Auditoría de enlaces internos.
- axe-core para accesibilidad.
- Lighthouse para rendimiento y buenas prácticas.

## 4. Portada alternativa

Archivo de prueba: `index-alternativo.html`.

Características:
- Mantiene las cuatro columnas oficiales: Crianza, INFORMÁTICA, Bienestar y Acompañamiento.
- Reutiliza imágenes locales WebP.
- Reutiliza el menú y el buscador global.
- Obtiene las lecturas recientes desde `data/catalogo.json`.
- No introduce fuentes tipográficas, iconos, scripts ni imágenes de terceros.
- Incluye navegación por teclado, foco visible, contraste, estados de carga y respeto por movimiento reducido.
- No cambia el `index.html` principal.

## 5. Estrategia de búsqueda

Fase actual: buscador global que consulta el catálogo editorial y el índice de alimentos.

Prueba propuesta:
1. Construir un índice Pagefind en una rama de prueba, sobre el sitio ya construido en `dist/`.
2. Medir el peso del índice y el tiempo de respuesta en red lenta.
3. Verificar acentos, sinónimos y errores ortográficos frecuentes.
4. Comparar resultados con el buscador global actual.
5. Mantener la búsqueda especializada de alimentos.
6. Solo integrar Pagefind si mejora la recuperación de artículos sin empeorar carga ni navegación.

No ejecutar la prueba en el workflow de producción hasta que exista una evaluación aprobada.

## 6. Estrategia de disponibilidad

Antes de añadir Workbox:
1. Inspeccionar el sitio publicado y el APK/WebView.
2. Confirmar si el contenedor registra su propio Service Worker.
3. Definir qué se puede almacenar: portada, CSS/JS, imágenes esenciales y artículos consultados.
4. Evitar cachear respuestas personales o contenido dinámico no validado.
5. Probar actualización de versiones, limpieza y recuperación tras desconexión.
6. Verificar que el almacenamiento no crezca sin límite.

## 7. Flujo de cambios

- Las propuestas se desarrollan en ramas independientes.
- No sobrescribir la portada de producción para hacer pruebas visuales.
- Cada cambio debe incluir su validación.
- La incorporación a `main` requiere revisión explícita.
- La publicación sigue dependiendo del workflow actual y de la salida `dist/`.

## 8. Fuera del alcance de esta fase

- Migrar a React, Vue, Angular u otro framework.
- Añadir bases de datos o backend.
- Añadir Cloudflare Workers.
- Reemplazar el motor editorial.
- Modificar artículos científicos o su contenido.
- Cambiar el dominio o la configuración de Pages.
