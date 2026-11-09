# CIBA · Worker del recetario

Este directorio contiene el código fuente versionado del Worker de Cloudflare.

## Estado de esta etapa

El endpoint `POST /interpret` usa Workers AI (Gemma 4) únicamente para interpretar texto libre y mapearlo a IDs de alimentos candidatos que ya existen en la biblioteca CIBA.

**No genera recetas, cantidades, sustituciones ni recomendaciones pediátricas.** La interfaz debe mostrar los alimentos reconocidos para confirmación humana.

## Despliegue manual inicial

1. Abrir el Worker `ciba-recetario-api` en Cloudflare.
2. Entrar en **Edit code**.
3. Sustituir todo el código por el contenido completo de `index.js`.
4. Comprobar que el binding se llama exactamente `AI`.
5. Pulsar **Deploy**.
6. Probar `GET /` y después integrar el cliente para enviar `POST /interpret`.

El endpoint permite solicitudes CORS solo desde `https://ciba1000dias-lab.github.io`. CORS no sustituye límites de abuso del proveedor; antes de abrir el endpoint al público deben configurarse límites de frecuencia en Cloudflare.

## Pruebas locales

Desde este directorio, ejecutar `npm test` con Node.js 20 o posterior.


## Estado real del despliegue (9 nov 2026)

El Worker de Cloudflare ya existe, tiene el binding `AI` y superó una prueba manual de generación con Gemma 4. Sin embargo, el código que está publicado en Cloudflare sigue siendo el código de prueba con la ruta `?test=1`. El archivo `index.js` de este directorio es la siguiente versión preparada, pero **todavía no se ha desplegado**.

No sustituir el Worker activo hasta revisar las pruebas y configurar límites de frecuencia. CORS no es un control de autenticación.
