# CIBA · Activación del acceso por correo

## Arquitectura
- Supabase Auth gestiona cuentas de personas adultas y enlaces mágicos de un solo uso.
- Resend entrega los correos transaccionales mediante SMTP.
- GitHub Pages continúa sirviendo la web estática.

## Estado
La interfaz y el flujo están preparados, pero el envío permanece desactivado hasta conectar el proyecto. No se han guardado credenciales ni secretos en el repositorio.

## 1. Supabase
1. Crear un proyecto en https://supabase.com/dashboard.
2. Authentication → URL Configuration:
   - Site URL: https://ciba1000dias-lab.github.io/ciba2.0/
   - Redirect URL: https://ciba1000dias-lab.github.io/ciba2.0/plataforma/mi-cuenta/acceso/
3. Authentication → Sign In / Providers: habilitar Email y Magic Link.
4. Mantener la confirmación de correo activa; no habilitar auto-confirm.

El plan Free incluye 50.000 usuarios activos mensuales, pero los proyectos gratuitos pueden pausarse tras una semana de inactividad. El SMTP predeterminado de Supabase es solo para pruebas: 2 correos por hora y solo a direcciones autorizadas del equipo.

## 2. Resend
1. Crear una cuenta en https://resend.com/signup.
2. Añadir y verificar un dominio que CIBA controle en https://resend.com/domains.
3. Publicar los registros DNS SPF y DKIM indicados por Resend y configurar DMARC.
4. Crear una API key para SMTP.

El plan gratuito publicado ofrece 3.000 correos al mes y 100 al día. Para enviar a usuarios reales se necesita un dominio remitente verificado; github.io no es un dominio que CIBA pueda verificar como propio.

## 3. Configurar SMTP en Supabase
En Project Settings → Authentication → SMTP Settings:
- Sender name: CIBA
- Sender email: una dirección del dominio verificado
- Host: smtp.resend.com
- Port: 465
- Username: resend
- Password: la API key SMTP de Resend

La contraseña SMTP/API key se introduce solo en el panel seguro de Supabase. Nunca se guarda en GitHub, JavaScript o HTML. Tras activar SMTP personalizado, revisar límites de envío y configurar CAPTCHA/antiabuso.

## 4. Conectar el frontend
En Supabase → Project Settings → API, copiar Project URL y Publishable key (o anon public legacy key) y colocarlas en assets/js/ciba-auth-config.js.
Solo estos dos valores públicos se exponen al navegador. Nunca usar service_role, secret key ni una clave de Resend en ese archivo.

## 5. Plantilla del correo
Copiar docs/plantilla-correo-acceso-ciba.html en Authentication → Email Templates → Magic Link. Conservar {{ .ConfirmationURL }}.

## 6. Antes de abrir el registro
- Revisar y aprobar la política de privacidad y el aviso de tratamiento de datos.
- Activar CAPTCHA y comprobar límites de envío.
- Probar registro, acceso, enlaces caducados/reutilizados, cierre de sesión y correos no recibidos.
- No guardar información de menores ni crear tablas de perfiles hasta diseñar y activar políticas RLS y revisar la protección de datos.
- Separar correo de autenticación de futuros boletines comerciales.

Documentación:
- https://supabase.com/docs/guides/auth/auth-email-passwordless
- https://supabase.com/docs/guides/auth/auth-smtp
- https://resend.com/docs/send-with-smtp
- https://supabase.com/pricing
- https://resend.com/pricing
