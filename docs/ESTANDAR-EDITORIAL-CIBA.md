# CIBA · Sistema editorial y tipográfico común

Versión 1.0 · Fase I · 20 de noviembre de 2026

Este documento establece la base visual y funcional compartida por CRIANZA, INFORMÁTICA, BIENESTAR y ACOMPAÑAMIENTO. Unificar no significa homogeneizar sus identidades: cada columna conserva su color, voz, portada y recursos propios; las páginas interiores comparten jerarquía, legibilidad, navegación y comportamiento móvil.

## 1. Identidad de las cuatro columnas

| Columna | Color rector | Referencia cromática del sistema | Criterio |
|---|---|---|---|
| CRIANZA 💚 | Verde | Noche #172b27 · verde #526e56 · oro #d9b878 | Cálida, cercana, natural |
| INFORMÁTICA 💙 | Azul | Azul profundo #12364d · azul #174f70 · oro #d5b879 | Digital, clara, confiable |
| BIENESTAR 💛 | Amarillo/dorado | Base oscura #493a32 · ocre #8c671f · oro #d9b878 | Preventiva, luminosa, serena |
| ACOMPAÑAMIENTO ❤️ | Rojo/terracota | Base oscura #493a32 · rojo #a9443b · terracota #c66b5e | Humana, acogedora, respetuosa |

Los tonos de base, papel y texto se mantienen coordinados con cada portada existente. No se sustituyen portadas aprobadas ni se cambia la paleta de INFORMÁTICA por la paleta verde general.

## 2. Jerarquía de páginas

1. **Portada de columna:** presenta propósito, identidad cromática, introducción y acceso a sus áreas.
2. **Página de área/sección:** explica el alcance de esa área y organiza sus subsecciones o artículos.
3. **Página de subsección:** presenta una temática delimitada y enlaza sus artículos individuales.
4. **Artículo:** desarrolla una sola pieza editorial, con sus fuentes, imágenes, multimedia, recursos e interactivos propios.

Cada nivel debe tener página y URL propias. No se agrupan varios artículos como un único documento continuo. Las páginas auxiliares y herramientas de PLATAFORMA conservan su arquitectura funcional y no se convierten en columnas editoriales.

## 3. Tipografía y lectura

- Títulos y encabezados: Georgia / serif clásica, con peso regular y jerarquía clara.
- Texto corrido, navegación, controles y metadatos: Arial/Helvetica/sans-serif.
- Texto base móvil: 16 px como referencia; interlineado aproximado 1.7–1.8.
- H1: 36–62 px adaptable; H2: 24–32 px; H3: 19–24 px.
- Párrafos breves, listas cuando faciliten la acción y bloques de lectura con anchura cómoda.
- Evitar párrafos íntegramente en mayúsculas, texto diminuto y contraste bajo.

## 4. Componentes comunes

- **Kicker/etiqueta:** identifica columna, área, subsección o tipo de contenido.
- **Hero/cabecera:** título, bajada y color rector de la columna.
- **Tarjetas:** fondo claro, borde discreto, radio moderado y enlace claramente identificable.
- **Notas y alertas:** jerarquía visual y color semántico; no depender solo del color para transmitir advertencias.
- **Botones y enlaces:** texto descriptivo, estados hover/focus y área táctil mínima de 44 px.
- **Tablas:** contenido legible en móvil; permitir desplazamiento horizontal cuando sea necesario.
- **Multimedia:** proporciones responsivas, texto alternativo, subtítulos/transcripción cuando corresponda y peso optimizado.
- **Migas de pan:** CIBA → columna → área → subsección (si existe) → página actual.

Clases reutilizables incorporadas por el sistema: `.ciba-estandar-kicker`, `.ciba-estandar-tarjeta`, `.ciba-estandar-nota`, `.ciba-estandar-boton` y `.ciba-estandar-migas`.

## 5. Navegación global

El menú hamburguesa y el Oráculo/buscador son elementos globales persistentes. Deben estar disponibles en portada, áreas, subsecciones y artículos, sin duplicar sus implementaciones locales. Los enlaces del menú deben llevar a páginas individuales y sus rutas deben funcionar desde cualquier profundidad.

Las migas complementan, pero no sustituyen, el menú global. Ningún componente fijo debe tapar títulos, controles, contenido ni avisos en pantallas pequeñas.

## 6. Diseño móvil y conectividad limitada

- Enfoque mobile-first; sin exigir desplazamiento horizontal de toda la página.
- Imágenes y vídeos fluidos; evitar recursos decorativos pesados.
- Controles accesibles con teclado y tacto.
- Respetar `prefers-reduced-motion`.
- Mantener el contenido esencial disponible sin depender de animaciones o scripts secundarios.
- No introducir frameworks pesados ni nuevas dependencias.
- Comprobar que el menú, Oráculo, enlaces, reproductores y elementos interactivos no se solapen en anchos pequeños.

## 7. Requisitos editoriales y sanitarios

- Un artículo aborda un tema central y tiene título, bajada, desarrollo, cierre y fuentes verificables cuando corresponda.
- La evidencia y la seguridad infantil prevalecen sobre recursos decorativos.
- No se inventan recomendaciones clínicas ni se altera contenido aprobado durante una tarea de diseño.
- Las advertencias deben expresarse también con texto claro.
- La plataforma ofrece educación parental; no sustituye evaluación ni consulta individual.

## 8. Metadatos y calidad técnica

Cada página debe tener `lang="es"`, viewport móvil, título SEO único, descripción pertinente, theme-color de su columna y rutas relativas correctas. El sistema de construcción incorpora el módulo global y las migas de navegación.

La normalización tipográfica agrega tokens y componentes comunes sin borrar el cuerpo editorial, los estilos propios, imágenes, SVG, audios, vídeos o interactivos. Es idempotente y se aplica únicamente a páginas de las cuatro columnas.

## 9. Criterios de aceptación

- [ ] Las cuatro columnas mantienen su identidad cromática.
- [ ] Los cuatro niveles editoriales tienen estructura de referencia.
- [ ] Tipografía, legibilidad, foco y áreas táctiles siguen un patrón común.
- [ ] Menú hamburguesa y Oráculo persisten en todas las pantallas editoriales.
- [ ] Migas y metadatos corresponden a la jerarquía real.
- [ ] Imágenes y multimedia son responsivas.
- [ ] No se alteran textos clínicos aprobados ni se pierden recursos.
- [ ] Las pruebas automáticas pasan y el despliegue termina correctamente.
- [ ] La revisión visual móvil queda registrada como comprobación separada; un build exitoso no equivale a inspección visual en un teléfono.

## 10. Modelos de referencia

Los esqueletos HTML de `docs/plantillas/` definen la estructura mínima de portada, área, subsección y artículo. Se adaptan al color de la columna y al contenido real; no son páginas para publicar literalmente.
