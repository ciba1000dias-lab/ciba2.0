# CIBA · Hoja de ruta técnica

> Propuesta de trabajo. Revisión: 27 de noviembre de 2026.

## Fase 0 · Protección y documentación
- [x] Revisar el repositorio y la portada actual.
- [x] Revisar arquitectura editorial, catálogo, buscador global y workflow.
- [x] Crear una rama de propuesta separada de `main`.
- [x] Documentar candidatos y licencias declaradas.
- [x] Crear una portada alternativa sin dependencias externas.
- [ ] Validar la portada alternativa en móvil y escritorio.
- [ ] Comparar visualmente con la portada actual antes de decidir.

## Fase 1 · Experiencia visual
- [ ] Revisar legibilidad, contraste y jerarquía visual.
- [ ] Validar navegación por teclado y lectores de pantalla.
- [ ] Auditar imágenes y peso total de la portada.
- [ ] Ejecutar axe-core y corregir incidencias reales.
- [ ] Ejecutar Lighthouse con perfil móvil.

## Fase 2 · Búsqueda
- [ ] Crear una prueba aislada de Pagefind sobre `dist/`.
- [ ] Medir tamaño de índice y carga en conexión lenta.
- [ ] Comparar precisión con el buscador actual.
- [ ] Comprobar búsqueda en artículos, fichas y contenidos con acentos.
- [ ] Decidir si Pagefind complementa o sustituye parte del buscador actual.
- [ ] Mantener el índice de alimentos y sus filtros especializados.

## Fase 3 · Disponibilidad sin conexión
- [ ] Auditar APK/WebView y Service Worker real.
- [ ] Diseñar política de caché y actualización.
- [ ] Probar Workbox solo en rama experimental.
- [ ] Verificar acceso offline a portada, navegación y artículos previamente consultados.
- [ ] Medir almacenamiento y comportamiento tras nuevas versiones.

## Fase 4 · Gobierno de dependencias
- [ ] Confirmar licencias y versiones exactas.
- [ ] Incorporar avisos de licencia cuando corresponda.
- [ ] Mantener este registro actualizado.
- [ ] Retirar dependencias que no aporten mejoras verificables.

## Criterios para considerar una fase terminada

- La navegación existente sigue funcionando.
- Los enlaces internos pasan la auditoría.
- No se introducen errores en pruebas automáticas.
- El sitio funciona en Android y con conexión limitada.
- La mejora se demuestra con una comparación o prueba.
- La portada de producción no se modifica sin aprobación.
