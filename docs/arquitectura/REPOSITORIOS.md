# CIBA · Catálogo de repositorios libres evaluados

> Documento técnico interno. Revisión inicial: 27 de noviembre de 2026.
> Este catálogo distingue herramientas evaluadas de dependencias realmente incorporadas. Estar listado no significa estar instalado.

## Criterios de selección

- Licencia abierta identificable y compatible con el uso previsto.
- Proyecto público, no archivado y con actividad de mantenimiento comprobable.
- Compatibilidad con HTML/CSS/JavaScript y el flujo estático actual.
- Carga reducida, uso móvil y posibilidad de servir archivos localmente.
- Sin servicios de pago, cuentas externas ni backend obligatorio.
- Integración gradual y reversible.

## Candidatos priorizados

| Proyecto | Licencia declarada en GitHub | Función | Encaje en CIBA | Estado |
|---|---|---|---|---|
| [Pagefind](https://github.com/Pagefind/pagefind) | MIT | Búsqueda estática de texto completo | Índice de artículos y búsqueda por contenido | Evaluar en entorno de pruebas |
| [Workbox](https://github.com/GoogleChrome/workbox) | MIT | Herramientas para Service Workers y caché | Mejorar lectura sin conexión | Evaluar después de auditar PWA actual |
| [Fuse.js](https://github.com/krisk/Fuse) | Apache-2.0 | Búsqueda difusa en JavaScript | Tolerancia a errores ortográficos en catálogos pequeños | Alternativa a Pagefind; no instalar ambos por defecto |
| [axe-core](https://github.com/dequelabs/axe-core) | MPL-2.0 | Auditoría automatizada de accesibilidad | Detectar barreras de navegación y lectura | Herramienta de desarrollo/CI |
| [Lighthouse](https://github.com/GoogleChrome/lighthouse) | Apache-2.0 | Auditoría de rendimiento y calidad web | Medir rendimiento móvil, accesibilidad y SEO | Herramienta de auditoría |
| [SortableJS](https://github.com/SortableJS/Sortable) | MIT | Reordenamiento táctil de listas | Posible herramienta editorial futura | No prioritario |

## Referencias visuales pendientes de verificación

- [Lucide](https://github.com/lucide-icons/lucide): biblioteca de iconos SVG. La respuesta de metadatos consultada no devolvió un identificador SPDX concluyente para el repositorio. No copiar ni empaquetar iconos hasta comprobar la licencia del archivo o paquete concreto.
- [Marked](https://github.com/markedjs/marked): parser Markdown. El campo de licencia del repositorio consultado devolvió `NOASSERTION`; verificar la licencia de la versión y paquete antes de incorporarlo.
- Pico CSS no se propone como dependencia: no se ha completado aquí una comprobación fiable de su estado de mantenimiento y licencia. Preferimos un sistema CSS propio, pequeño y coherente con la identidad CIBA.

## Reglas de incorporación

1. Revisar licencia y versión exacta antes de copiar, empaquetar o distribuir código.
2. Fijar versión; no utilizar ramas flotantes ni CDN como dependencia de producción.
3. Descargar el recurso necesario y alojarlo localmente cuando sea técnicamente viable.
4. Medir tamaño añadido, impacto de carga y compatibilidad móvil.
5. Mantener una alternativa funcional si la biblioteca no carga.
6. Registrar versión, licencia, archivos incorporados y fecha de revisión en `DEPENDENCIAS.md`.
7. Retirar la biblioteca si no aporta una mejora medible o compromete la estabilidad.

## Fuentes técnicas

- GitHub Pagefind: https://github.com/Pagefind/pagefind
- GitHub Workbox: https://github.com/GoogleChrome/workbox
- GitHub Fuse.js: https://github.com/krisk/Fuse
- GitHub axe-core: https://github.com/dequelabs/axe-core
- GitHub Lighthouse: https://github.com/GoogleChrome/lighthouse
- GitHub SortableJS: https://github.com/SortableJS/Sortable
