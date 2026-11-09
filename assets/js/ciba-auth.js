(() => {
  'use strict';

  const root = location.pathname.split('/plataforma/')[0] + '/';
  const app = document.getElementById('ciba-auth-app');
  if (!app) return;

  const addStyle = (path, id) => {
    if (document.getElementById(id)) return;
    const link = document.createElement('link');
    link.id = id;
    link.rel = 'stylesheet';
    link.href = root + path;
    document.head.appendChild(link);
  };

  addStyle('assets/css/ciba-plataforma.css', 'ciba-plataforma-css');
  addStyle('assets/css/ciba-auth.css', 'ciba-auth-css');

  const safe = value => String(value || '').replace(/[&<>"']/g, char => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[char]));

  const home = root + 'index.html';
  const platform = root + 'plataforma/';
  const accessUrl = root + 'plataforma/mi-cuenta/acceso/index.html';
  const profileUrl = root + 'plataforma/mi-cuenta/perfil/';

  app.innerHTML = `
    <header class="plataforma-top ciba-auth-top">
      <div class="plataforma-top-inner">
        <a class="plataforma-logo" href="${home}" aria-label="CIBA, inicio">CIBA</a>
        <a class="plataforma-volver" href="${platform}">← Plataforma</a>
      </div>
    </header>

    <section class="plataforma-hero ciba-auth-hero">
      <div class="plataforma-wrap ciba-auth-hero-inner">
        <div class="plataforma-kicker">CIBA · Un espacio para acompañar</div>
        <h1>Tu camino en CIBA.<br><em>Más cerca, más sencillo.</em></h1>
        <p>Accede a tu espacio personal de forma segura y continúa explorando conocimiento para los primeros 1000 días.</p>
        <div class="ciba-auth-hero-note"><span>✧</span> Un acceso personal. Sin contraseñas que recordar.</div>
      </div>
    </section>

    <main class="plataforma-main ciba-auth-main">
      <nav class="plataforma-breadcrumb" aria-label="Ruta de navegación">
        <a href="${home}">Inicio</a><span>›</span>
        <a href="${platform}">Plataforma</a><span>›</span>
        <a href="${platform}mi-cuenta/">Mi cuenta</a><span>›</span>
        <strong>Acceso</strong>
      </nav>

      <section class="ciba-auth-layout" aria-labelledby="ciba-auth-title">
        <div class="ciba-auth-card">
          <div class="ciba-auth-emblema" aria-hidden="true">
            <span>✧</span>
            <svg viewBox="0 0 100 100"><path d="M50 50 C50 37 68 36 72 49 C80 72 51 84 34 69 C12 49 27 19 53 17 C83 14 97 47 84 71"/></svg>
          </div>
          <div class="ciba-auth-kicker">Tu espacio personal</div>
          <h2 id="ciba-auth-title">Inicia sesión</h2>
          <p class="ciba-auth-intro">Entra con tu cuenta de Google. Si todavía no formas parte de CIBA, tu cuenta se creará durante el primer acceso.</p>

          <button id="ciba-auth-google" class="ciba-auth-google" type="button" disabled>
            <svg viewBox="0 0 48 48" aria-hidden="true">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.75 7.18l7.73 6C44.43 37.96 46.98 31.82 46.98 24.55z"/>
              <path fill="#FBBC05" d="M10.53 28.59A14.4 14.4 0 0 1 9.75 24c0-1.59.27-3.13.76-4.59l-7.98-6.19A23.9 23.9 0 0 0 0 24c0 3.87.93 7.53 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.91-5.8l-7.73-6c-2.14 1.44-4.89 2.3-8.18 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </svg>
            <span>Continuar con Google</span><b>→</b>
          </button>

          <div id="ciba-auth-status" class="ciba-auth-status pending" role="status" aria-live="polite">
            <strong>Estamos preparando el acceso.</strong>
            <span>La conexión se activará al completar la configuración segura de Google y Supabase.</span>
          </div>
          <div id="ciba-auth-session" class="ciba-auth-session" hidden></div>

          <div class="ciba-auth-divider"><span>Tu privacidad importa</span></div>
          <p class="ciba-auth-privacy">El acceso identifica únicamente a la persona adulta. En esta etapa CIBA no solicita datos de niños ni información clínica.</p>
          <p class="ciba-auth-help">¿Aún no tienes cuenta? No necesitas registrarte antes: el primer acceso con Google la crea automáticamente.</p>
        </div>

        <aside class="ciba-auth-aside">
          <div class="ciba-auth-aside-symbol">◈</div>
          <h3>Un espacio que crece contigo</h3>
          <p>Estamos construyendo herramientas para que puedas guardar recursos, adaptar tu recorrido y volver fácilmente a los contenidos que te acompañan.</p>
          <ul>
            <li><span>01</span> Acceso sencillo y seguro.</li>
            <li><span>02</span> Tu sesión puede mantenerse activa.</li>
            <li><span>03</span> Tus datos personales se tratan con prudencia.</li>
          </ul>
          <a href="${platform}">Conoce la plataforma <span>↗</span></a>
        </aside>
      </section>

      <p class="ciba-auth-back"><a href="${platform}mi-cuenta/">← Volver a Mi cuenta</a></p>
    </main>

    <footer class="plataforma-pie">CIBA · Conocimiento, confianza y acompañamiento · <a href="${home}">Inicio</a></footer>
  `;

  const googleButton = document.getElementById('ciba-auth-google');
  const status = document.getElementById('ciba-auth-status');
  const sessionBox = document.getElementById('ciba-auth-session');
  let client = null;

  const showStatus = (kind, title, message) => {
    status.className = 'ciba-auth-status ' + kind;
    status.innerHTML = '<strong>' + safe(title) + '</strong><span>' + safe(message) + '</span>';
    status.hidden = false;
  };

  const showSession = session => {
    if (!session || !session.user) {
      sessionBox.hidden = true;
      googleButton.hidden = false;
      return;
    }
    googleButton.hidden = true;
    status.hidden = true;
    sessionBox.hidden = false;
    const email = session.user.email || 'Cuenta Google';
    sessionBox.innerHTML = `
      <div class="ciba-auth-session-mark">✓</div>
      <h3>Ya estás dentro de CIBA</h3>
      <p>Sesión iniciada con <strong>${safe(email)}</strong>.</p>
      <a class="ciba-auth-profile" href="${profileUrl}">Continuar a mi espacio <span>→</span></a>
      <button type="button" id="ciba-auth-signout" class="ciba-auth-signout">Cerrar sesión</button>
    `;
    document.getElementById('ciba-auth-signout').addEventListener('click', async () => {
      const { error } = await client.auth.signOut();
      if (error) showStatus('error', 'No pudimos cerrar la sesión', 'Inténtalo nuevamente.');
      else {
        showSession(null);
        showStatus('success', 'Sesión cerrada', 'Puedes volver a entrar cuando lo necesites.');
      }
    });
  };

  const init = async () => {
    try {
      const { supabase: sharedClient } = await import(root + 'assets/js/ciba-supabase.js');
      client = sharedClient;

      const { data, error } = await client.auth.getSession();
      if (error) throw error;
      showSession(data.session);
      if (data.session) return;

      googleButton.disabled = false;
      showStatus('ready', 'Acceso disponible', 'Continúa con Google. Si es tu primera vez, CIBA creará tu cuenta de forma automática.');

      client.auth.onAuthStateChange((_event, session) => showSession(session));

      googleButton.addEventListener('click', async () => {
        googleButton.disabled = true;
        googleButton.classList.add('loading');
        showStatus('pending', 'Conectando con Google', 'Te estamos llevando al proceso seguro de identificación.');
        try {
          const { error: authError } = await client.auth.signInWithOAuth({
            provider: 'google',
            options: { redirectTo: accessUrl }
          });
          if (authError) throw authError;
        } catch (error) {
          console.error('CIBA Google Auth:', error);
          showStatus('error', 'No pudimos iniciar sesión', (error && error.message) || 'Inténtalo nuevamente dentro de unos minutos.');
          googleButton.disabled = false;
          googleButton.classList.remove('loading');
        }
      });
    } catch (error) {
      console.error('CIBA Auth configuration:', error);
      showStatus('error', 'No se pudo iniciar el acceso', 'La configuración no está disponible en este momento. Inténtalo más tarde.');
    }
  };

  init();
})();
