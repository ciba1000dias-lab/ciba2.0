# CIBA · Mi bebé crece
## Especificación funcional y técnica

**Ruta pública reservada:** `/b/recursos/seguimiento-crecimiento/`  
**Ubicación:** Recursos especiales · BIENESTAR  
**Población inicial:** nacimiento a 24 meses  
**Modalidades:** familiar y avanzada  
**Estado:** especificación aprobada para desarrollo por etapas  
**Principio rector:** acompañar y organizar el seguimiento; nunca diagnosticar ni sustituir la consulta pediátrica.

## 1. Propósito

Ofrecer a madres, padres y cuidadores una herramienta móvil, ligera y comprensible para registrar mediciones, observar tendencias, conocer hitos del desarrollo, preparar controles pediátricos y conservar un resumen personal del seguimiento del niño.

No es una historia clínica electrónica, no permite comunicación clínica de urgencia y no transmite datos infantiles a servidores.

## 2. Modos de uso

### 2.1 Modo familiar (predeterminado)
- Inicio con el nombre o apodo elegido para el niño y su edad calculada.
- Resumen sencillo de los últimos registros.
- Explicaciones en lenguaje cotidiano, sin clasificar al niño como sano o enfermo.
- Diario de logros y calendario de controles.
- Mensajes de orientación sobre cuándo consultar.

### 2.2 Modo avanzado (optativo)
- Historial completo de mediciones.
- Gráficas de trayectoria con curvas de referencia OMS.
- Puntuación Z y percentil, solo cuando exista dato de referencia válido para sexo, edad y medición.
- Información metodológica, fecha y versión de las tablas.
- Exportación de un informe para compartir voluntariamente con el pediatra.

El modo avanzado no convierte a la familia en evaluadora clínica. Los resultados se presentan como referencias poblacionales y no como diagnósticos.

## 3. Perfil infantil y cálculo de edad

Datos mínimos:
- Nombre/apodo opcional.
- Fecha de nacimiento.
- Sexo requerido por las tablas antropométricas de referencia (categorías de las curvas OMS).
- Prematuridad: sí/no.
- Edad gestacional al nacimiento, en semanas y días, si nació antes de 37 semanas.

La fecha de nacimiento y los demás datos se procesan en el dispositivo. La edad cronológica se calcula con fecha local, sin redondear meses de forma engañosa. Si se registra prematuridad, se muestra también la edad corregida calculada desde la edad gestacional; el usuario puede consultar ambas. El algoritmo y los límites de uso de la corrección deben recibir revisión pediátrica antes de activar resultados antropométricos avanzados.

Se permite más de un perfil infantil. El nombre es opcional y no se solicitan apellidos, documento de identidad, dirección, teléfono ni datos de contacto.

## 4. Registro antropométrico

Cada registro contendrá fecha, valor, unidad, indicador, observación opcional y procedencia declarada (control de salud / medición familiar / dato histórico).

Indicadores de la primera versión:
- Peso para la edad.
- Longitud para la edad.
- Peso para la longitud.
- Perímetro cefálico para la edad.

Reglas:
- Peso en kg, con conversión segura desde gramos.
- Longitud recumbente en cm para menores de 24 meses.
- Perímetro cefálico en cm.
- Validación de valores positivos, fechas no futuras y unidades explícitas.
- Detección de registros duplicados o mediciones incompatibles; nunca corregir silenciosamente.
- El peso para longitud solo se calcula dentro del rango cubierto por la tabla de referencia.
- No mostrar IMC como indicador de clasificación en esta primera versión para menores de 24 meses.
- Una medición aislada nunca produce una conclusión sobre el estado de salud.

## 5. Referencias y motor antropométrico

Base de referencia: Estándares de Crecimiento Infantil de la OMS (WHO Child Growth Standards), con tablas LMS por sexo e indicador. La primera implementación debe usar archivos tabulares versionados, integrados localmente, con atribución visible y procedencia documentada.

Indicadores que se habilitarán únicamente después de verificar las tablas:
1. Peso para la edad.
2. Longitud para la edad.
3. Peso para longitud.
4. Perímetro cefálico para la edad.

El motor debe:
- Seleccionar la tabla correcta por indicador y sexo.
- Interpolar únicamente según un método documentado y validado cuando la edad o longitud caiga entre filas tabuladas.
- Calcular Z con el método LMS: si L ≠ 0, Z = ((X/M)^L − 1)/(L·S); si L = 0, Z = ln(X/M)/S.
- Convertir Z a percentil mediante una función de distribución normal probada.
- Rechazar parámetros ausentes, no finitos, fuera de rango o incompatibles.
- No extrapolar fuera de los límites oficiales.
- Mostrar «no calculable con la referencia disponible» en vez de inventar un resultado.
- Conservar precisión interna; redondear solo para presentación.
- Incluir pruebas de referencia contra ejemplos publicados y un segundo cálculo independiente.

La tabla no se considerará lista por el simple hecho de cargar un CSV: se verificará fila a fila, sexo, unidades, intervalos, extremos, datos faltantes y resultados de prueba. La interpretación de Z y percentiles deberá revisarse editorialmente antes de habilitarse para familias.

## 6. Gráficas

- Gráfica separada por indicador.
- Curvas OMS y puntos de medición individual claramente diferenciados.
- Ejes y unidades visibles, fechas legibles en pantallas pequeñas.
- Tooltip accesible al tocar cada punto: fecha, valor y observación.
- Opción para ocultar/mostrar las curvas de referencia.
- Sin colores de «aprobado/reprobado» ni semáforos que etiqueten al niño.
- Mensaje permanente: importa la trayectoria y el contexto clínico; una gráfica no establece diagnóstico.

## 7. Desarrollo infantil

Sección educativa de 0 a 24 meses, organizada en seis ventanas: 0–3, 4–6, 7–9, 10–12, 13–18 y 19–24 meses.

Dimensiones:
- Movimiento y postura.
- Comunicación y lenguaje.
- Cognición y exploración.
- Interacción y desarrollo socioemocional.

Cada habilidad tendrá fuente, edad/ventana de referencia y redacción revisada. El registro familiar será «lo he observado», «todavía no lo observo» o «no estoy seguro». No se calculará una puntuación global ni se emitirá una etiqueta de retraso. La ausencia de una habilidad aislada no equivale a un diagnóstico. Se indicará cuándo conversar con el equipo de salud o solicitar evaluación del desarrollo.

Las ventanas de logro motor de la OMS pueden complementar el contenido, pero no deben confundirse con una lista completa de evaluación del desarrollo.

## 8. Controles, diario y exportación

- Calendario de controles con fecha, motivo opcional y notas.
- Diario de logros con fecha y texto breve; fotografías no incluidas en la primera versión.
- Historial cronológico de mediciones y controles.
- Informe imprimible/PDF con perfil mínimo, edad cronológica y corregida cuando aplique, tabla de mediciones, gráficas habilitadas, notas y fuentes.
- Exportación/restauración voluntaria mediante archivo local cifrado o formato JSON con advertencia de privacidad; no sincronización en la nube en la primera versión.
- Función clara para eliminar un perfil y todos sus datos del dispositivo.

## 9. Seguridad y mensajes de orientación

La herramienta no hace triaje automatizado ni calcula riesgo clínico. Los avisos se activan por reglas de integridad de datos (por ejemplo, valor imposible, unidad errónea, dato fuera del rango tabulado) y por contenido educativo revisado.

Debe explicar que se solicite valoración pediátrica si hay preocupación por crecimiento, pérdida de habilidades, dificultades de alimentación o desarrollo, o cambios sostenidos en la trayectoria. Las señales de emergencia tendrán un mensaje independiente, inequívoco y orientado a buscar atención urgente; nunca se retrasará la atención por completar la herramienta.

No se enviarán notificaciones que puedan interpretarse como diagnóstico o alarma clínica automática.

## 10. Privacidad y funcionamiento

- Almacenamiento local mediante IndexedDB.
- Sin cuentas, analítica conductual, publicidad, API externa ni envío de datos personales.
- Aviso antes de exportar o compartir un archivo.
- Opción de borrar todos los datos.
- Interfaz responsiva, accesible, con controles táctiles amplios y contraste suficiente.
- El recurso debe poder abrirse con conexión lenta. El funcionamiento sin conexión completo dependerá de que la página y sus recursos se hayan cargado previamente y de la política de caché del sitio/PWA; no se prometerá hasta probarlo en Android real.
- La pérdida, limpieza o desinstalación de datos del navegador puede eliminar el almacenamiento local; la exportación voluntaria será la vía de respaldo.

## 11. Arquitectura de integración

- Página especial estática dentro de CIBA 2.0, no artículo convencional.
- Ruta pública: `/b/recursos/seguimiento-crecimiento/`.
- Interfaz y lógica propias, con datos de referencia separados del HTML.
- Ningún cambio a las cuatro columnas, al catálogo de artículos ni a las rutas editoriales existentes.
- Integración en los accesos de Recursos especiales solo después de validar el recurso.
- Construcción y publicación mediante el flujo GitHub Pages existente; no publicar tablas antropométricas sin pruebas y atribución.

## 12. Etapas y puertas de calidad

**Etapa 1 — Experiencia y datos locales:** perfil infantil, selector de modo, panel familiar, registro de mediciones, historial y diario. Sin percentiles ni interpretación automática.

**Etapa 2 — Referencias OMS:** incorporación de tablas oficiales LMS, motor de cálculo, interpolación documentada, gráficas y pruebas independientes. No se activa hasta completar validación numérica.

**Etapa 3 — Desarrollo infantil:** ventanas educativas, registro de habilidades, fuentes y mensajes de consulta revisados.

**Etapa 4 — Calendario e informe:** controles, exportación PDF/JSON, restauración y eliminación segura.

**Etapa 5 — Calidad y publicación:** pruebas móviles, accesibilidad, privacidad, funcionamiento offline real, auditoría de enlaces, revisión pediátrica/editorial y publicación con etiqueta «EN REVISIÓN EDITORIAL» hasta aprobación final.

## 13. Criterios de aceptación

- Perfil y datos se conservan tras cerrar y reabrir la página en el mismo dispositivo/navegador.
- Se pueden registrar varios niños sin mezclar sus datos.
- Los errores de fecha, unidad y valores se detectan sin borrar registros.
- Los cálculos OMS coinciden con casos de referencia publicados y pruebas independientes.
- No se extrapola fuera de los rangos tabulados.
- Las gráficas son comprensibles en un teléfono de pantalla pequeña.
- No se emite diagnóstico, clasificación de salud ni puntuación de desarrollo.
- Exportación y restauración conservan los registros y muestran advertencias de privacidad.
- Borrar un perfil elimina sus datos locales.
- No se transmite información infantil a servidores.
- La publicación no altera los contenidos ni las rutas editoriales existentes.

## 14. Referencias base

- WHO. Child Growth Standards: https://www.who.int/tools/child-growth-standards
- WHO. WHO Anthro Manual, versión 3.2.2: https://www.who.int/docs/default-source/child-growth/child-growth-standards/software/anthro-pc-manual-v322.pdf
- CDC. WHO Growth Charts Data Files (tablas LMS y CSV para peso/edad, longitud/edad, peso/longitud y perímetro cefálico/edad, nacimiento a 24 meses): https://www.cdc.gov/growthcharts/who-data-files.htm
- CDC. Using WHO Growth Standard Charts: https://www.cdc.gov/growth-chart-training/hcp/using-growth-charts/who-using.html

**Nota:** esta especificación define el alcance. Los datos LMS, los algoritmos, los hitos y los mensajes clínicos requieren validación antes de habilitarse para uso familiar.
