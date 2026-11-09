# CIBA · Arquitectura de inteligencia artificial para «¿Qué cocino hoy?»

**Decisión técnica:** utilizar Cloudflare Workers AI como primera plataforma de inferencia, sujeto a crear una cuenta gratuita y validar el modelo y sus cuotas desde la cuenta real.  
**Modelo inicial a evaluar:** `@cf/google/gemma-4-26b-a4b-it`.  
**Alternativa a evaluar en pruebas:** `@cf/zai-org/glm-4.7-flash`, si la cuota gratuita y la calidad en español resultan mejores.  
**Fecha de decisión:** 9 de noviembre de 2026.

## 1. Por qué Cloudflare

La documentación oficial consultada indica:

- Workers AI ofrece una asignación de 10.000 Neurons diarios en el plan Workers Free. Al superar la cuota, las operaciones de IA se detienen hasta el siguiente reinicio; no es necesario pasar al plan de pago.
- Workers Free incluye hasta 100.000 solicitudes diarias.
- Workers AI puede conectarse a un Worker o a una Pages Function mediante un binding `AI`.
- Gemma 4 26B A4B está disponible en Workers AI; la ficha declara soporte multilingüe, function calling y Zero Data Retention.
- El modelo y la asignación gratuita deben comprobarse en el panel de la cuenta antes de habilitar el servicio público. Las cuotas y modelos pueden cambiar.

Fuentes oficiales:
- Precios Workers AI: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Límites Workers Free: https://developers.cloudflare.com/workers/platform/limits/
- Inicio Workers AI: https://developers.cloudflare.com/workers-ai/get-started/
- Binding para Pages Functions: https://developers.cloudflare.com/pages/functions/bindings/
- Ficha Gemma 4 26B A4B: https://developers.cloudflare.com/workers-ai/models/gemma-4-26b-a4b-it/
- Secretos de Workers: https://developers.cloudflare.com/workers/configuration/secrets/

## 2. Arquitectura elegida

CIBA continuará alojado como sitio estático en GitHub Pages. La IA se expondrá mediante un Worker independiente en Cloudflare, por ejemplo bajo un subdominio `workers.dev`.

Flujo:

1. La interfaz CIBA recoge edad o fecha de nacimiento, ingredientes escritos y respuestas sobre alergias/restricciones.
2. El navegador calcula la edad localmente. No envía fecha de nacimiento: envía únicamente el tramo/edad calculado.
3. Un módulo local normaliza ingredientes, resuelve sinónimos y contrasta con el catálogo de alimentos CIBA.
4. El cliente envía al Worker solo los datos mínimos necesarios y el contexto editorial curado.
5. El Worker valida formato, tamaño, origen permitido, cuota y frecuencia de solicitudes.
6. El Worker invoca Workers AI mediante binding `env.AI`; no expone token de Cloudflare ni credenciales en el frontend.
7. El modelo devuelve una respuesta estructurada. El backend valida el esquema y comprueba que la receta propuesta exista en el catálogo autorizado.
8. Las reglas deterministas de CIBA bloquean cualquier incompatibilidad crítica. La IA no puede anularlas.
9. La interfaz presenta la propuesta, advertencias y referencias bibliográficas ya asociadas a la receta aprobada.

## 3. Papel de la IA

La IA podrá:

- comprender lenguaje natural en español cubano;
- interpretar errores ortográficos, puntuación, sinónimos y expresiones habituales;
- pedir aclaraciones cuando un ingrediente sea ambiguo;
- identificar qué alimentos mencionados corresponden al catálogo CIBA;
- seleccionar entre recetas previamente revisadas;
- explicar por qué una receta coincide con los ingredientes;
- adaptar la explicación y los pasos al nivel de comprensión de la familia;
- sugerir preguntas aclaratorias y alternativas que estén explícitamente autorizadas en los datos.

La IA NO podrá:

- inventar recetas, ingredientes, cantidades, tiempos de cocción o sustituciones;
- declarar seguro un alimento por inferencia;
- establecer diagnósticos, tratamientos o pautas nutricionales clínicas;
- inventar fuentes ni enlaces;
- recomendar introducción de alimentos contra las reglas de edad;
- ignorar alergias, restricciones o advertencias;
- sustituir las reglas deterministas de seguridad.

**Principio técnico:** el modelo conversa y razona sobre datos aprobados; el catálogo y el motor de reglas deciden qué se puede mostrar.

## 4. Datos mínimos y privacidad

- No pedir nombre, dirección, teléfono ni identificadores.
- No transmitir ni almacenar la fecha de nacimiento; calcular edad en el navegador.
- No conservar conversaciones ni ingredientes enviados en la primera versión.
- No incluir datos personales en prompts, logs ni métricas.
- Informar de que el texto escrito se procesa por un proveedor externo de IA (Cloudflare) para generar la respuesta.
- Revisar términos, privacidad y retención del proveedor antes de producción. La ficha del modelo indica Zero Data Retention, pero no debe interpretarse como una garantía universal sobre todos los componentes de la plataforma.
- Configurar CORS para aceptar solo el dominio oficial de CIBA.
- Limitar tamaño del cuerpo, longitud de texto, tokens de salida, frecuencia de peticiones y concurrencia.
- Añadir protección contra abuso y respuestas de error que no revelen información interna.

## 5. Controles de seguridad

La aplicación no debe confiar en la salida del modelo como si fuera validación clínica.

Antes de enviar:
- comprobar edad y etapa;
- detectar alergias/restricciones declaradas;
- reconocer ingredientes ambiguos o no catalogados;
- bloquear peticiones de consejo médico, tratamiento o dietas clínicas individualizadas;
- evitar que texto del usuario modifique las instrucciones internas del sistema.

Después de recibir:
- validar JSON y esquema estricto;
- comprobar IDs de receta y alimentos contra el catálogo;
- verificar edad autorizada, alérgenos, ingredientes prohibidos y advertencias;
- rechazar cualquier salida que invente una referencia o no pase las reglas;
- mostrar «no encontramos una opción segura» si no hay coincidencia válida.

Casos que requieren bloqueo o derivación profesional: alergias diagnosticadas o reacción alérgica, prematuridad con necesidades especiales, disfagia, enfermedad metabólica o renal, dieta terapéutica, fallo de medro/problemas de crecimiento, enfermedad aguda relevante o instrucciones médicas específicas.

## 6. Proveedores alternativos investigados

- **Google Gemini API:** ofrece un nivel gratuito con límites, pero su documentación indica que el contenido del nivel gratuito puede utilizarse para mejorar productos de Google. No es la primera opción para este caso.
  https://ai.google.dev/gemini-api/docs/pricing
- **OpenRouter modelos gratuitos:** útil para prototipos, pero los modelos gratuitos tienen límites (la documentación consultada indica 20 solicitudes/minuto y 50/día para variantes `:free`) y disponibilidad variable.
  https://openrouter.ai/collections/free-models/
- **Hugging Face Inference Providers:** la cuenta gratuita recibe créditos mensuales muy pequeños (documentación consultada: USD 0,10, sujeto a cambios), por lo que no sirve como backend gratuito continuo.
  https://huggingface.co/docs/inference-providers/pricing
- **Groq:** ofrece API rápida y límites por modelo y organización; las cuotas exactas dependen del modelo y de la cuenta. Puede servir como respaldo experimental, pero no se elige hasta verificar términos de privacidad y límites aplicables.
  https://console.groq.com/docs/rate-limits

## 7. Condiciones de gratuidad

CIBA no debe habilitar facturación automática ni solicitar tarjeta para la primera versión. Utilizar exclusivamente el plan gratuito y la cuota gratuita de Workers AI. Configurar alertas/controles disponibles y límites propios conservadores. Si se agota la cuota, mostrar un mensaje amable y mantener accesibles la biblioteca y el catálogo estático; nunca cambiar silenciosamente a un servicio de pago.

Antes de conectar el proveedor:
1. Crear cuenta gratuita de Cloudflare.
2. Confirmar que Workers AI está disponible en el plan sin tarjeta y revisar la cuota visible.
3. Habilitar Workers AI y obtener los datos de despliegue necesarios.
4. Crear el Worker con binding AI y CORS restringido.
5. Desplegarlo y probarlo con casos sintéticos antes de conectar la interfaz pública.

## 8. Pruebas de aceptación

- Español cubano, tildes omitidas, faltas frecuentes, puntuación, singular/plural y sinónimos.
- Entradas ambiguas: debe preguntar, no adivinar.
- Intentos de prompt injection: no deben alterar reglas ni instrucciones.
- Edad inferior a 6 meses: nunca sugerir alimentación complementaria.
- Miel antes de 12 meses, alimentos con riesgo de atragantamiento, ingredientes crudos y alérgenos: bloqueos probados.
- Respuesta de IA con receta o fuente inexistente: rechazada.
- Sin cuota, error del proveedor o desconexión: no inventar respuesta; informar y ofrecer la biblioteca.
- Peticiones desde dominios ajenos: rechazadas.
- No aparecen claves, datos personales ni contenido sensible en frontend, repositorio o logs.

## 9. Estado

La arquitectura está seleccionada como propuesta técnica, pero el servicio todavía no está conectado ni desplegado. Requiere una cuenta Cloudflare gratuita del propietario del proyecto y pruebas reales de disponibilidad/cuota. No anunciar el recetario como «IA activa» hasta superar las pruebas de aceptación.
