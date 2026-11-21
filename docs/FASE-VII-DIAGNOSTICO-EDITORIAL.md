# Fase VII · Diagnóstico y consolidación editorial de CIBA

Fecha de corte: 21 de noviembre de 2026  
Repositorio: `ciba1000dias-lab/ciba2.0`  
Rama base auditada: `main`

## 1. Propósito

Establecer una línea base verificable de la arquitectura editorial de las cuatro columnas de CIBA, distinguir páginas de sección de artículos individuales, identificar vacíos estructurales y proponer un orden de trabajo para la consolidación editorial.

Este documento es un diagnóstico de estructura. **La existencia de un archivo HTML no equivale a publicación, aprobación clínica ni aprobación editorial.** No se cambia el estado de ningún artículo ni su contenido clínico.

## 2. Inventario estructural

El inventario se obtuvo del árbol completo de archivos de `main`, revisando las páginas `index.html` de cada área y sus páginas descendientes.

| Columna | Áreas previstas/identificadas | Páginas individuales encontradas | Situación estructural |
|---|---:|---:|---|
| CRIANZA | 7 áreas (C1–C7) | 115 | Las siete áreas tienen páginas individuales. C1 conserva además páginas auxiliares temáticas. |
| INFORMÁTICA | 10 áreas (I1–I10) | 67 | Las diez áreas tienen páginas individuales. |
| BIENESTAR | 10 áreas (B1–B10) | 40 | Hay artículos individuales en B1–B6. B7–B10 muestran esquemas temáticos, pero todavía no tienen páginas individuales de artículo. |
| ACOMPAÑAMIENTO | 10 áreas anunciadas en su portada | 0 | Solo existen páginas de área A1–A5 y son páginas de preparación. A6–A10 no tienen todavía directorios/páginas de área. |

**Total estructural localizado: 222 páginas individuales de artículo** en CRIANZA, INFORMÁTICA y BIENESTAR. Este total no clasifica su estado editorial.

### 2.1 CRIANZA

| Área | Páginas individuales |
|---|---:|
| C1 · Alimentación y lactancia | 40 |
| C2 · Sueño y descanso | 15 |
| C3 · Cuidados básicos y autonomía | 15 |
| C4 · Juego, estimulación y aprendizaje | 12 |
| C5 · Vínculo, apego y desarrollo socioemocional | 12 |
| C6 · Prevención y seguridad en el hogar | 10 |
| C7 · Cultura, rutinas y vida cotidiana | 11 |
| **Total** | **115** |

C1 contiene, además, páginas auxiliares de navegación, fonoteca, alimentación y recursos de la plataforma. No deben confundirse con artículos individuales.

### 2.2 INFORMÁTICA

| Área | Páginas individuales |
|---|---:|
| I1 · Alfabetización sanitaria digital | 7 |
| I2 · Desinformación y consejos virales | 6 |
| I3 · Privacidad y seguridad infantil en redes | 7 |
| I4 · Pantallas y desarrollo | 7 |
| I5 · Inteligencia artificial e infancias | 6 |
| I6 · Redes sociales y salud mental familiar | 7 |
| I7 · Apps, plataformas y herramientas digitales | 5 |
| I8 · Telemedicina y comunicación digital | 8 |
| I9 · Contenido infantil y consumo audiovisual | 7 |
| I10 · Ciudadanía digital y futuro | 7 |
| **Total** | **67** |

La columna presenta una estructura de diez áreas con páginas individuales. La revisión posterior debe centrarse en coherencia, actualización de referencias, enlaces y consistencia de recursos, sin alterar su identidad visual azul.

### 2.3 BIENESTAR

Se localizaron 40 páginas individuales en B1–B6. Las áreas B7–B10 ya contienen páginas de área con esquemas y títulos de temas previstos, pero esos temas no están desarrollados todavía como páginas individuales.

- B7 · Enfermedades frecuentes en la primera infancia.
- B8 · Señales de alarma y urgencias.
- B9 · Salud bucal y hábitos saludables.
- B10 · Salud ambiental y prevención de riesgos clínicos.

Los índices de B7–B10 declaran expresamente que sus artículos están planificados y no tienen enlaces activos. Se deben crear páginas individuales para cada artículo aprobado, sin convertir los encabezados del índice en un artículo continuo.

La línea «Hábitos saludables y prevención» debe permanecer dentro de BIENESTAR, sin crear una quinta columna principal. Los contenidos sobre hogar libre de humo, exposición infantil al tabaco, residuos del tabaco y apoyo para dejar de fumar se integrarán en esta línea y se coordinarán con B10 para evitar duplicaciones.

### 2.4 ACOMPAÑAMIENTO

La portada anuncia diez áreas:

1. Apoyo emocional a la familia.
2. Corresponsabilidad y familia.
3. Redes de apoyo y comunidad.
4. Cuidado del cuidador.
5. Acompañamiento práctico y seguimiento.
6. Crianza a distancia y migración.
7. Abuelos y cuidadores.
8. Familias diversas y situaciones especiales.
9. Duelo, pérdida y situaciones difíciles.
10. Comunidad CIBA y acompañamiento entre familias.

En el repositorio solo están creadas las páginas A1–A5. Las cinco se identifican como espacios en preparación y no contienen artículos individuales. A6–A10 aparecen en la portada, pero todavía no tienen páginas de área propias.

Esto constituye la brecha estructural más importante de la columna y requiere completar primero su arquitectura antes de anunciarla como biblioteca desarrollada.

## 3. Hallazgos transversales

1. Las cuatro columnas tienen una arquitectura editorial reconocible, pero su grado de desarrollo es desigual.
2. CRIANZA e INFORMÁTICA son las columnas con mayor cobertura estructural de artículos individuales.
3. BIENESTAR está parcialmente desarrollado: B1–B6 tienen páginas individuales; B7–B10 permanecen como esquemas temáticos.
4. ACOMPAÑAMIENTO es, por ahora, una estructura de áreas en preparación, no una biblioteca de artículos.
5. Las portadas pueden dar una impresión de cobertura completa cuando las páginas individuales todavía no existen. Los indicadores de avance deben diferenciar áreas planificadas, áreas con página, artículos redactados, artículos revisados y artículos publicados.
6. La revisión de estados editoriales debe realizarse desde cada `meta.json` y el contenido visible; no debe inferirse a partir de la presencia de `index.html`.

## 4. Orden de trabajo recomendado

### Prioridad 1 · Cerrar la brecha de BIENESTAR

- Mantener B7–B10 como cuatro áreas separadas, con una página por artículo.
- Desarrollar B8 (señales de alarma y urgencias) con especial atención a mensajes claros, seguros y clínicamente revisados.
- Continuar B7 (enfermedades frecuentes) y luego B9 (salud bucal) y B10 (salud ambiental).
- Integrar «Hábitos saludables y prevención» dentro de BIENESTAR y coordinar los temas de tabaco con B10.
- No publicar material clínico nuevo sin aprobación clínica explícita.

### Prioridad 2 · Construir ACOMPAÑAMIENTO como biblioteca real

- Crear las páginas de área A6–A10 y normalizar A1–A5.
- Sustituir las páginas de preparación por páginas de área con navegación y catálogo real.
- Priorizar inicialmente A1–A5 por su relación directa con la experiencia cotidiana de familias durante los primeros mil días.
- Definir para cada área una lista cerrada de artículos, sus códigos, objetivos, recursos y referencias antes de redactar en serie.
- Mantener el enfoque de apoyo respetuoso y no juzgador; no presentar el acompañamiento digital como sustituto de servicios profesionales o redes presenciales.

### Prioridad 3 · Consolidación de CRIANZA e INFORMÁTICA

- Realizar una pasada editorial de consistencia de títulos, resúmenes, referencias, fechas, recursos y enlaces entre artículos.
- Verificar que cada artículo tenga página individual, migas de pan, enlaces anterior/siguiente y retorno a su área.
- Preservar los estilos propios de cada columna, especialmente el azul de INFORMÁTICA.
- No crear artículos nuevos por volumen si no responden a un vacío editorial demostrado.

## 5. Sistema de seguimiento editorial propuesto

Cada contenido debe registrarse en una matriz única con estos campos:

- Código y título editorial.
- Columna, área y subsección.
- Tipo: artículo, página de área, recurso o página auxiliar.
- Estado estructural: planificado / página creada / página individual creada.
- Estado editorial: borrador / revisión editorial / aprobado.
- Estado clínico, cuando corresponda: pendiente / revisado / aprobado.
- Multimedia: fotografía, ilustración, video, audio, infografía e interactivo, según pertinencia.
- Fuentes y fecha de última revisión.
- URL pública y resultado de comprobación.
- Responsable y próxima acción.

Los estados estructurales, editoriales, clínicos y de publicación deben mantenerse separados. No se deben eliminar etiquetas ni cambiar estados por inferencia.

## 6. Criterios de aceptación de la Fase VII

La fase se considerará consolidada cuando:

- Las diez áreas anunciadas en BIENESTAR y ACOMPAÑAMIENTO tengan una página de área coherente con su contenido real.
- Cada artículo anunciado como disponible tenga su propia página individual y navegación funcional.
- Los artículos planificados estén identificados como tales y no aparezcan como publicados.
- Los estados editoriales y clínicos estén completos y sean verificables.
- Cada columna conserve su identidad visual, arquitectura, menú global y Oráculo.
- Los recursos multimedia e interactivos sean pertinentes, ligeros y comprobables.
- La matriz editorial permita medir el avance real sin confundir páginas, artículos y estados.

## 7. Alcance de este diagnóstico

Este documento registra una línea base del árbol de archivos de `main` a 21 de noviembre de 2026. No certifica la revisión clínica de los artículos, la disponibilidad de enlaces externos ni la inspección visual en dispositivos físicos. Tampoco modifica artículos ni estados editoriales.

**Conclusión:** el siguiente esfuerzo de CIBA debe concentrarse en completar BIENESTAR y construir ACOMPAÑAMIENTO como bibliotecas reales, mientras se mantiene CRIANZA e INFORMÁTICA mediante control de calidad y actualización. La prioridad es cerrar brechas de cobertura con calidad, no aumentar el número de páginas por sí mismo.
