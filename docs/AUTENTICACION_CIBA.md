# CIBA · Activación del acceso con Google

## Arquitectura
- Supabase Auth gestiona las cuentas de personas adultas.
- Google OAuth permite iniciar sesión y crear cuentas nuevas sin que CIBA envíe correos.
- GitHub Pages continúa sirviendo la web estática.
- El frontend usa únicamente Project URL y Publishable/anon public key. Los secretos permanecen en los paneles de los proveedores.

## Estado actual
La interfaz de acceso, el botón Google OAuth y el acceso en cabecera están implementados. El inicio de sesión público todavía no está activo: faltan las credenciales del proyecto Supabase y la configuración OAuth de Google. No se han guardado credenciales ni secretos en el repositorio.

## 1. Crear el proyecto Supabase
1. Crear un proyecto en https://supabase.com/dashboard.
2. En Authentication → URL Configuration:
   - Site URL: https://ciba1000dias-lab.github.io/ciba2.0/
   - Redirect URL: https://ciba1000dias-lab.github.io/ciba2.0/plataforma/mi-cuenta/acceso/index.html
3. En Authentication → Sign In / Providers, habilitar Google.

## 2. Crear las credenciales OAuth de Google
1. Abrir https://console.cloud.google.com/.
2. Crear o seleccionar un proyecto de Google Cloud.
3. Configurar OAuth consent screen / Google Auth Platform, completar el nombre de la aplicación CIBA y los datos de contacto requeridos.
4. Crear un OAuth Client ID de tipo Web application.
5. En Authorized JavaScript origins añadir:
   - https://ciba1000dias-lab.github.io
6. En Authorized redirect URIs copiar exactamente la URL de callback que muestra Supabase en Authentication → Sign In / Providers → Google. No usar la URL de GitHub Pages como callback de Google.
7. Copiar el Client ID y Client Secret al formulario de configuración del proveedor Google dentro de Supabase y guardar.
8. Mientras la aplicación OAuth esté en modo Testing, añadir las cuentas de prueba permitidas. Antes de abrirla al público, completar la verificación/publicación que Google solicite y revisar los alcances pedidos.

## 3. Conectar Supabase con el frontend
En Supabase → Project Settings → API, copiar:
- Project URL.
- Publishable key (o anon public key legacy).

Colocar únicamente esos dos valores en assets/js/ciba-auth-config.js:
- SUPABASE_URL
- SUPABASE_ANON_KEY

La clave pública/anon está diseñada para usarse en el navegador, siempre con las políticas de seguridad apropiadas. Nunca colocar service_role, secret key, Client Secret de Google ni claves SMTP en JavaScript, HTML o GitHub.

## 4. Capacidad y plan
El plan Free de Supabase incluye una cuota de 50.000 usuarios activos mensuales (MAU), no un límite de 25 registros al día. CIBA no debe imponer un tope artificial de 25 registros diarios. Revisar las cuotas vigentes de autenticación, base de datos, almacenamiento y tráfico en https://supabase.com/pricing antes de ampliar el uso. Los proyectos gratuitos pueden pausarse tras periodos de inactividad según las condiciones vigentes del servicio.

## 5. Antes de abrir el registro
- Revisar y aprobar la política de privacidad y el aviso de tratamiento de datos.
- Comprobar que el proveedor Google está habilitado y que el consentimiento OAuth está publicado/configurado para usuarios externos.
- Probar alta nueva, inicio de sesión, persistencia de sesión, cierre de sesión y retorno a CIBA.
- Configurar protección antiabuso disponible en Supabase y vigilar el uso/las cuotas.
- No guardar información de menores ni crear tablas de perfiles hasta diseñar y activar políticas RLS y revisar la protección de datos.
- No afirmar que el acceso está operativo públicamente hasta completar una prueba real con una cuenta externa.

## Documentación
- https://supabase.com/docs/guides/auth/social-login/auth-google
- https://supabase.com/docs/guides/auth/redirect-urls
- https://supabase.com/pricing
- https://developers.google.com/identity/protocols/oauth2
