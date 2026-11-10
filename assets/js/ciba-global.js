
// CIBA · SISTEMA GLOBAL
// Navegación principal y buscador ancestral.

(() => {
  'use strict';

  if (window.__CIBA_GLOBAL_INICIADO__) return;
  window.__CIBA_GLOBAL_INICIADO__ = true;

  const RAIZ = new URL('../../', import.meta.url);
  const RUTA_CATALOGO = new URL('data/catalogo.json', RAIZ);
  const RUTA_ALIMENTOS = new URL('assets/data/alimentos-busqueda.json', RAIZ);
  const RUTA_CSS = new URL('../css/ciba-global.css?v=20261110-18', import.meta.url);

  let catalogo = null;
  let alimentos = null;
  let menuAbierto = false;
  let scrollOculto = false;
  let transicionActiva = false;

  function actualizarVisibilidadBuscador() {
    const buscador = document.querySelector('.ciba-global-buscador');
    if (!buscador) return;
    buscador.classList.toggle(
      'ciba-oraculo-oculto',
      menuAbierto || scrollOculto || transicionActiva
    );
  }

  const columnas = [
    { id: 'C', titulo: 'Crianza' },
    { id: 'I', titulo: 'Internet' },
    { id: 'B', titulo: 'Bienestar' },
    { id: 'A', titulo: 'Acompañamiento' }
  ];

  function elemento(etiqueta, clase, texto) {
    const nodo = document.createElement(etiqueta);
    if (clase) nodo.className = clase;
    if (texto !== undefined) nodo.textContent = texto;
    return nodo;
  }

  function enlace(ruta, texto, clase = '') {
    const nodo = elemento('a', clase, texto);
    nodo.href = ruta;
    return nodo;
  }

  function normalizar(texto) {
    return String(texto || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();
  }

  function urlPublica(ruta) {
    return new URL(
      String(ruta || '').replace(/^\/+/, ''),
      RAIZ
    ).href;
  }

  function esPortada() {
    const actual = window.location.pathname.replace(/index\.html$/, '');
    return actual === RAIZ.pathname;
  }

  function cargarEstilos() {
    if (document.getElementById('ciba-global-css')) return;

    const css = document.createElement('link');
    css.id = 'ciba-global-css';
    css.rel = 'stylesheet';
    css.href = RUTA_CSS.href;
    document.head.appendChild(css);
  }

  async function obtenerCatalogo() {
    if (catalogo) return catalogo;

    const respuesta = await fetch(RUTA_CATALOGO.href, {
      cache: 'no-cache'
    });

    if (!respuesta.ok) {
      throw new Error('No se pudo cargar el catálogo de CIBA.');
    }

    catalogo = await respuesta.json();
    return catalogo;
  }

  async function obtenerAlimentos() {
    if (alimentos) return alimentos;

    const respuesta = await fetch(RUTA_ALIMENTOS.href, { cache: 'no-cache' });
    if (!respuesta.ok) throw new Error('No se pudo cargar el índice de búsqueda de alimentos.');
    const indice = await respuesta.json();
    if (!Array.isArray(indice.alimentos)) throw new Error('Índice de búsqueda de alimentos inválido.');
    alimentos = indice;
    return alimentos;
  }

  function resolverSeccion(consulta) {
    const q = normalizar(consulta);
    const reglas = [
      { clave: 'preparaciones-cubanas', etiqueta: 'Preparaciones cubanas del arroz', patrones: ['congri', 'moros y cristianos', 'moros', 'arroz amarillo', 'arroz con pollo', 'arroz con vegetales', 'arroz con frijoles'] },
      { clave: 'edad', etiqueta: 'Edad de introducción', patrones: ['edad', 'desde cuando', 'a partir de cuando', 'cuando introducir', 'cuando puedo', 'meses puede', 'a que edad'] },
      { clave: 'preparacion', etiqueta: 'Preparación según la etapa', patrones: ['preparar', 'preparacion', 'como dar', 'como ofrecer', 'textura', 'trozos', 'pure', 'papilla', 'aplastar', 'triturar', 'cortar para'] },
      { clave: 'seguridad', etiqueta: 'Preparación segura', patrones: ['lavar', 'limpiar', 'quitar semillas', 'quitar cascara', 'seguro', 'segura', 'hueso'] },
      { clave: 'precauciones', etiqueta: 'Precauciones', patrones: ['precaucion', 'precauciones', 'alergia', 'alergico', 'atragantamiento', 'peligro', 'riesgo', 'evitar', 'contraindicacion'] },
      { clave: 'recetas', etiqueta: 'Recetas sencillas', patrones: ['receta', 'recetas', 'que puedo cocinar', 'cocinar', 'que puedo preparar'] },
      { clave: 'conservacion', etiqueta: 'Conservación', patrones: ['conservar', 'conservacion', 'guardar', 'nevera', 'refrigerar', 'cuanto dura', 'congelar', 'almacenar'] },
      { clave: 'beneficios', etiqueta: 'Beneficios', patrones: ['beneficio', 'beneficios', 'para que sirve', 'es bueno', 'bueno para'] },
      { clave: 'propiedades', etiqueta: 'Propiedades nutricionales', patrones: ['propiedad', 'propiedades', 'vitamina', 'vitaminas', 'nutriente', 'nutrientes', 'fibra', 'proteina', 'calorias', 'grasa', 'composicion', 'nutricional'] },
      { clave: 'fuentes', etiqueta: 'Fuentes y referencias', patrones: ['fuente', 'fuentes', 'referencia', 'referencias', 'bibliografia', 'evidencia'] },
      { clave: 'video', etiqueta: 'Video relacionado', patrones: ['video', 'youtube', 'short'] },
      { clave: 'descripcion', etiqueta: 'Información general', patrones: ['que es', 'informacion general', 'descripcion', 'describe'] }
    ];
    return reglas.find((regla) => regla.patrones.some((patron) => q.includes(patron))) || null;
  }

  function cerrarMenu(panel, boton) {
    menuAbierto = false;
    actualizarVisibilidadBuscador();
    panel.classList.remove('abierto');
    boton.setAttribute('aria-expanded', 'false');
    boton.setAttribute('aria-label', 'Abrir menú de navegación');
  }

  function crearSubmenu(titulo, opciones, panel) {
    const grupo = elemento('div', 'ciba-global-grupo');

    const encabezado = elemento(
      'a',
      'ciba-global-enlace',
      titulo
    );

    encabezado.href = '#';
    encabezado.setAttribute('aria-expanded', 'false');

    const lista = elemento('div', 'ciba-global-submenu');
    lista.hidden = true;

    encabezado.addEventListener('click', (evento) => {
      evento.preventDefault();

      const abierto = !lista.hidden;
      lista.hidden = abierto;
      encabezado.setAttribute('aria-expanded', String(!abierto));
    });

    opciones.forEach((opcion) => {
      const item = elemento(
        'a',
        'ciba-global-enlace ciba-global-subenlace',
        opcion
      );

      item.href = '#';
      item.setAttribute('aria-disabled', 'true');
      item.title = 'Apartado en preparación';

      item.addEventListener('click', (evento) => {
        evento.preventDefault();
      });

      lista.appendChild(item);
    });

    grupo.append(encabezado, lista);
    panel.appendChild(grupo);
  }

  function resolverColumnaActual() {
    const ruta = window.location.pathname;
    const coincidencia = ruta.match(/\/(?:c|i|b|a)\/([CIBA])\d?\//i);
    let id = coincidencia ? coincidencia[1].toUpperCase() : '';
    if (!id) {
      const articulo = document.querySelector('.ciba-articulo');
      const clase = articulo ? Array.from(articulo.classList).find(x => /^articulo-(crianza|internet|bienestar|acompanamiento)$/.test(x)) : '';
      const equivalencias = { 'articulo-crianza':'C', 'articulo-internet':'I', 'articulo-bienestar':'B', 'articulo-acompanamiento':'A' };
      id = equivalencias[clase] || '';
    }
    if (window.location.pathname.includes('/plataforma/')) return { id:'', titulo:'Plataforma' };
    return columnas.find(c => c.id === id) || { id:'', titulo:'Explora CIBA' };
  }

  function crearCabeceraGlobal() {
    if (esPortada() || document.querySelector('.ciba-global-cabecera')) return null;

    // Las páginas de sección conservaban su cabecera antigua además de la global.
    // Retiramos solo esa cabecera superior para evitar que la marca aparezca duplicada.
    document.querySelectorAll('header.cabecera').forEach((anterior) => {
      anterior.remove();
    });

    const actual = resolverColumnaActual();
    const colores = { C:'#397653', I:'#287B9A', B:'#8C671F', A:'#A9443B' };
    if (actual.id) document.body.dataset.cibaColumna = actual.id.toLowerCase();
    const cabecera = elemento('header','ciba-global-cabecera');
    cabecera.dataset.columna = actual.id;
    cabecera.style.setProperty('--ciba-columna-color', colores[actual.id] || '#493A32');
    cabecera.setAttribute('aria-label','Identidad y navegación de CIBA');
    const marca = elemento('a','ciba-global-marca','CIBA');
    marca.href = new URL('index.html',RAIZ).href;
    marca.setAttribute('aria-label','Volver al inicio de CIBA');
    const contexto = elemento('span','ciba-global-contexto',actual.titulo);
    contexto.style.setProperty('--ciba-columna-color',colores[actual.id] || '#493A32');
    contexto.dataset.columna = actual.id;
    cabecera.append(marca,contexto);
    document.body.insertBefore(cabecera,document.body.firstChild);
    document.body.classList.add('ciba-con-cabecera-global');
    return cabecera;
  }

  function activarTransicionColumnas() {
    const colores = { C:'#397653', I:'#287B9A', B:'#8C671F', A:'#A9443B' };
    document.addEventListener('click', evento => {
      const ancla = evento.target.closest('a[href]');
      if (!ancla || evento.defaultPrevented || evento.button !== 0 || evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) return;
      const destino = new URL(ancla.href,window.location.href);
      const actual = resolverColumnaActual().id;
      const siguiente = (destino.pathname.match(/\/c\/([CIBA])\d?\//i) || [])[1]?.toUpperCase();
      if (!siguiente || !actual || siguiente === actual || destino.origin !== location.origin) return;
      evento.preventDefault();
      const velo = elemento('div','ciba-transicion-columnas');
      velo.style.setProperty('--color-origen',colores[actual]);
      velo.style.setProperty('--color-destino',colores[siguiente]);
      velo.innerHTML = '<span class="ciba-transicion-luz"></span><svg viewBox="0 0 100 100" aria-hidden="true"><path d="M50 50 C50 35 70 38 70 52 C70 72 43 78 30 60 C10 32 43 10 66 20 C95 32 92 70 70 84 C42 103 8 78 13 45"/></svg>';
      document.body.appendChild(velo);
      requestAnimationFrame(()=>velo.classList.add('activa'));
      window.setTimeout(()=>{ window.location.href = destino.href; },680);
    });
  }

  function crearMenu() {
    if (document.querySelector('.ciba-global-menu')) return;

    const cabeceraGlobal = crearCabeceraGlobal();
    const contenedor = elemento('div', 'ciba-global-menu');

    const boton = elemento('button', 'ciba-global-menu-boton');
    boton.type = 'button';
    boton.setAttribute('aria-label', 'Abrir menú de navegación');
    boton.setAttribute('aria-expanded', 'false');
    boton.setAttribute('aria-controls', 'ciba-menu-panel');

    for (let i = 0; i < 3; i++) {
      boton.appendChild(elemento('span'));
    }

    const panel = elemento('nav', 'ciba-global-panel');
    panel.id = 'ciba-menu-panel';
    panel.setAttribute('aria-label', 'Navegación principal');

    panel.appendChild(
      elemento('h2', 'ciba-global-menu-titulo', 'EXPLORA CIBA')
    );

    // INICIO
    panel.appendChild(
      enlace(
        new URL('index.html', RAIZ).href,
        'Inicio CIBA',
        'ciba-global-enlace'
      )
    );

    // ACCESO DIRECTO A LA BIBLIOTECA DE ALIMENTOS
    panel.appendChild(
      enlace(
        new URL('c/C1/alimentos/', RAIZ).href,
        'Biblioteca de alimentos',
        'ciba-global-enlace'
      )
    );

    // SUBSECCIÓN DE ALIMENTACIÓN DURANTE LA GESTACIÓN
    panel.appendChild(
      enlace(
        new URL('c/C1/alimentacion-gestacion/', RAIZ).href,
        'Alimentación durante la gestación',
        'ciba-global-enlace'
      )
    );

    // SUEÑO Y DESCANSO DURANTE LOS PRIMEROS DOS AÑOS
    panel.appendChild(
      enlace(
        new URL('c/C1/C1-03/', RAIZ).href,
        'Sueño infantil: horas y descanso seguro',
        'ciba-global-enlace'
      )
    );

    // ACCESO DIRECTO AL RECETARIO INTERACTIVO
    panel.appendChild(
      enlace(
        new URL('c/C1/recetario/', RAIZ).href,
        '¿Qué cocino hoy? · Recetario IA',
        'ciba-global-enlace'
      )
    );

    // CUATRO COLUMNAS
    columnas.forEach((columna) => {
      const grupo = elemento('div', 'ciba-global-grupo');

      const encabezado = elemento(
        'a',
        'ciba-global-enlace',
        ''
      );

      encabezado.href = new URL('index.html#areas', RAIZ).href;

      const letra = elemento(
        'span',
        'ciba-global-letra',
        columna.id
      );

      const nombre = elemento('span', '', columna.titulo);

      encabezado.append(letra, nombre);
      grupo.appendChild(encabezado);
      panel.appendChild(grupo);
    });

    // NAYARA Y TUREY
    const dudas = enlace(
      '#',
      'Las dudas de Nayara y Turey',
      'ciba-global-enlace'
    );

    dudas.setAttribute('aria-disabled', 'true');
    dudas.title = 'Página en preparación';

    dudas.addEventListener('click', (evento) => {
      evento.preventDefault();
    });

    panel.appendChild(dudas);

    // BUSCADOR
    const buscar = enlace(
      '#',
      'BUSCADOR CIBA',
      'ciba-global-enlace'
    );

    buscar.addEventListener('click', (evento) => {
      evento.preventDefault();
      // La opción BUSCADOR del menú debe poder invocar el oráculo
      // aunque este se hubiera ocultado durante el desplazamiento.
      scrollOculto = false;
      cerrarMenu(panel, boton);

      if (esPortada()) {
        abrirBuscadorDePortada();
      } else {
        const oraculo = document.querySelector(
          '.ciba-global-oraculo'
        );

        if (oraculo) oraculo.click();
      }
    });

    panel.appendChild(buscar);

    // PLATAFORMA: navegación jerárquica con rutas reales.
    const seccionesPlataforma = [["sobre-ciba","Sobre CIBA","Conoce el propósito, las personas y los principios que dan forma a CIBA.","✺",[["mision-y-lema","Misión y lema","La razón de ser de CIBA, su compromiso con las familias y el sentido de su lema."],["fundador","Fundador","La historia, motivación y visión de quien impulsa el proyecto."],["desarrolladores","Desarrolladores","El equipo técnico y las personas que construyen y mantienen la plataforma."],["colaboradores","Colaboradores","Profesionales e instituciones que contribuyen al crecimiento de CIBA."],["declaracion-editorial","Declaración editorial","Los principios de independencia, rigor, transparencia y revisión de los contenidos."]]],["confianza-y-legal","Confianza y legal","Información transparente sobre el uso responsable de CIBA, sus límites y la protección de las personas.","◈",[["aviso-medico","Aviso médico","Alcance educativo de la información y cuándo se necesita atención sanitaria individual."],["privacidad","Privacidad","Qué información podría recopilarse, para qué se utilizaría y cómo se protegería."],["datos-de-menores","Datos de menores","Principios reforzados de minimización, protección y tratamiento responsable de información infantil."],["terminos-de-uso","Términos de uso","Condiciones para utilizar la plataforma, sus recursos y herramientas."],["como-citar","Cómo citar","Orientaciones para citar artículos, recursos y materiales de CIBA."]]],["navegacion","Navegación","Herramientas para encontrar información y recorrer el conocimiento de CIBA de distintas maneras.","⌘",[["buscar","Buscar","Acceso al buscador de CIBA para localizar artículos, fichas y recursos."],["indice-tematico","Índice temático","Mapa organizado de temas, áreas y contenidos de las cuatro columnas."],["recorrido-por-edad","Recorrido por edad","Explorar contenidos desde la concepción hasta los dos años."],["series","Series","Colecciones de contenidos relacionados para profundizar paso a paso."],["glosario","Glosario","Definiciones claras de términos de salud, crianza, nutrición y desarrollo."]]],["comunidad","Comunidad","Canales para participar, enviar comentarios y ayudar a mejorar CIBA de forma respetuosa y segura.","♡",[["preguntale-al-pediatra","Pregúntale al pediatra","Un futuro espacio de orientación general que no sustituirá la consulta ni la atención urgente."],["reportar-error","Reportar error","Canal para comunicar enlaces rotos, errores de contenido o dificultades de uso."],["compartir","Compartir","Herramientas para compartir CIBA y sus recursos con otras familias y profesionales."],["unirse-al-equipo","Unirse al equipo","Conoce las formas de colaborar con CIBA como profesional, académico, comunicador, colaborador financiero o patrocinador."]]],["recursos","Recursos","Materiales complementarios para aprender, consultar y compartir información confiable.","✧",[["descargables","Descargables","Guías, fichas y materiales imprimibles para uso familiar y educativo."],["multimedia","Multimedia","Videos, audios, ilustraciones y otros formatos de aprendizaje."],["enlaces-recomendados","Enlaces recomendados","Selección editorial de recursos externos fiables y útiles."]]]];
    panel.appendChild(elemento('h2','ciba-global-menu-titulo ciba-global-menu-separador','PLATAFORMA'));
    panel.appendChild(enlace(urlPublica('plataforma/'),'Explorar Plataforma','ciba-global-enlace'));
    seccionesPlataforma.forEach((seccion) => {
      const grupo=elemento('div','ciba-global-grupo');
      const encabezado=elemento('a','ciba-global-enlace',seccion[1]);
      encabezado.href=urlPublica('plataforma/'+seccion[0]+'/');
      encabezado.setAttribute('aria-expanded','false');
      const lista=elemento('div','ciba-global-submenu');lista.hidden=true;
      encabezado.addEventListener('click',(evento)=>{evento.preventDefault();const abierto=!lista.hidden;lista.hidden=abierto;encabezado.setAttribute('aria-expanded',String(!abierto));});
      lista.appendChild(enlace(urlPublica('plataforma/'+seccion[0]+'/'),'Ver sección completa','ciba-global-enlace ciba-global-subenlace'));
      seccion[4].forEach(apartado=>lista.appendChild(enlace(urlPublica('plataforma/'+seccion[0]+'/'+apartado[0]+'/'),apartado[1],'ciba-global-enlace ciba-global-subenlace')));
      grupo.append(encabezado,lista);panel.appendChild(grupo);
    });


    boton.addEventListener('click', () => {
      const abierto = panel.classList.toggle('abierto');
      menuAbierto = abierto;

      if (abierto) {
        const panelBusqueda = document.querySelector('.ciba-global-panel-busqueda');
        const botonBusqueda = document.querySelector('.ciba-global-oraculo');
        if (panelBusqueda) panelBusqueda.classList.remove('abierto');
        if (botonBusqueda) botonBusqueda.setAttribute('aria-expanded', 'false');
      }
      actualizarVisibilidadBuscador();

      boton.setAttribute('aria-expanded', String(abierto));
      boton.setAttribute(
        'aria-label',
        abierto
          ? 'Cerrar menú de navegación'
          : 'Abrir menú de navegación'
      );
    });

    panel.addEventListener('click', (evento) => {
      if (
        evento.target.closest('a') &&
        !evento.target.closest('.ciba-global-grupo > a')
      ) {
        cerrarMenu(panel, boton);
      }
    });

    document.addEventListener('click', (evento) => {
      if (!contenedor.contains(evento.target)) {
        cerrarMenu(panel, boton);
      }
    });

    document.addEventListener('keydown', (evento) => {
      if (evento.key === 'Escape') {
        cerrarMenu(panel, boton);
      }
    });

    contenedor.append(boton, panel);
    if (cabeceraGlobal) cabeceraGlobal.appendChild(contenedor);
    else document.body.appendChild(contenedor);

    // Conectar cada columna con su primera área disponible.
    obtenerCatalogo()
      .then((datos) => {
        const grupos = panel.querySelectorAll(
          '.ciba-global-grupo'
        );

        columnas.forEach((columna, indice) => {
          const grupo = grupos[indice];
          if (!grupo) return;

          const encabezado = grupo.querySelector('a');

          const areas = (datos.areas || [])
            .filter((area) => area.columna === columna.id)
            .sort((a, b) => (a.orden || 0) - (b.orden || 0));

          if (areas.length) {
            encabezado.href = urlPublica(
              areas[0].ruta_publica
            );
          }
        });
      })
      .catch((error) => {
        console.warn(
          'CIBA: no se pudieron cargar las rutas de las columnas.',
          error
        );
      });
  }

  function abrirBuscadorDePortada() {
    const formulario = document.querySelector(
      '#form-busqueda, form.busqueda, .busqueda form'
    );

    const entrada = document.querySelector(
      '#consulta, input[type="search"]'
    );

    const destino = formulario ||
      document.querySelector('.busqueda');

    if (destino) {
      destino.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }

    if (entrada) {
      setTimeout(() => entrada.focus(), 400);
    }
  }

  function crearBuscador() {
    // La portada conserva su buscador normal.
    if (esPortada()) return;

    if (document.querySelector('.ciba-global-buscador')) return;

    const contenedor = elemento(
      'div',
      'ciba-global-buscador'
    );

    const boton = elemento(
      'button',
      'ciba-global-oraculo'
    );

    boton.type = 'button';
    boton.setAttribute(
      'aria-label',
      'Abrir buscador ancestral de CIBA'
    );
    boton.setAttribute('aria-expanded', 'false');
    boton.setAttribute(
      'aria-controls',
      'ciba-busqueda-panel'
    );

    const orbita = elemento(
      'span',
      'ciba-global-orbita'
    );

    const svg = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'svg'
    );

    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('class', 'ciba-global-espiral');
    svg.setAttribute('aria-hidden', 'true');

    const camino = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'path'
    );

    camino.setAttribute(
      'd',
      'M50 50 C50 35 70 38 70 52 C70 72 43 78 30 60 C10 32 43 10 66 20 C95 32 92 70 70 84 C42 103 8 78 13 45'
    );

    svg.appendChild(camino);
    boton.append(orbita, svg);

    const etiqueta = elemento(
      'span',
      'ciba-global-etiqueta',
      'CONSULTAR CIBA'
    );

    const panel = elemento(
      'section',
      'ciba-global-panel-busqueda'
    );

    panel.id = 'ciba-busqueda-panel';
    panel.setAttribute(
      'aria-label',
      'Buscador de CIBA'
    );

    const cabecera = elemento(
      'div',
      'ciba-global-busqueda-cabecera'
    );

    const titulo = elemento(
      'h2',
      'ciba-global-busqueda-titulo',
      'Explora CIBA'
    );

    const cerrar = elemento(
      'button',
      'ciba-global-cerrar',
      '×'
    );

    cerrar.type = 'button';
    cerrar.setAttribute(
      'aria-label',
      'Cerrar buscador'
    );

    cabecera.append(titulo, cerrar);

    const formulario = elemento(
      'form',
      'ciba-global-formulario'
    );

    const entrada = elemento(
      'input',
      'ciba-global-entrada'
    );

    entrada.type = 'search';
    entrada.placeholder = '¿Qué deseas encontrar?';
    entrada.setAttribute(
      'aria-label',
      'Buscar en CIBA'
    );
    entrada.autocomplete = 'off';
    entrada.required = true;

    const enviar = elemento(
      'button',
      'ciba-global-enviar',
      'BUSCAR'
    );

    enviar.type = 'submit';
    formulario.append(entrada, enviar);

    const resultados = elemento(
      'div',
      'ciba-global-resultados'
    );

    resultados.setAttribute('aria-live', 'polite');

    panel.append(cabecera, formulario, resultados);

    function cerrarPanel() {
      panel.classList.remove('abierto');
      boton.setAttribute('aria-expanded', 'false');
    }

    function abrirPanel() {
      panel.classList.add('abierto');
      boton.setAttribute('aria-expanded', 'true');

      setTimeout(() => entrada.focus(), 150);
    }

    boton.addEventListener('click', () => {
      if (panel.classList.contains('abierto')) {
        cerrarPanel();
      } else {
        abrirPanel();
      }
    });

    cerrar.addEventListener('click', cerrarPanel);

    formulario.addEventListener(
      'submit',
      async (evento) => {
        evento.preventDefault();

        const consulta = normalizar(entrada.value);
        if (!consulta) return;
        const palabrasIgnoradas = new Set(['mi','mis','el','la','los','las','un','una','unos','unas','puede','pueden','puedo','podria','dar','darle','ofrecer','ofrecerle','comer','para','desde','cuando','como','que','es','de','del','y','a','esta','este','bebe','bebes','mes','meses','ano','anos']);
        const terminos = consulta.split(/\s+/).filter((t) => t.length > 1 && !palabrasIgnoradas.has(t) && !/^\d+$/.test(t));
        const seccionSolicitada = resolverSeccion(consulta);

        resultados.replaceChildren(
          elemento(
            'p',
            'ciba-global-mensaje',
            'Consultando el conocimiento de CIBA...'
          )
        );

        try {
          const datos = await obtenerCatalogo();
          const datosAlimentos = await obtenerAlimentos().catch(() => ({ alimentos: [] }));
          const paginas = datos.paginas || [];

          // Buscar tanto artículos como fichas de la biblioteca de alimentos.
          const coincidencias = paginas.filter((pagina) => {
            const contenido = normalizar([
              pagina.titulo,
              pagina.descripcion,
              pagina.id,
              pagina.area,
              pagina.subseccion,
              ...(pagina.palabras_clave || [])
            ].join(' '));
            const aciertos = terminos.filter((termino) => contenido.includes(termino)).length;
            return terminos.length ? aciertos / terminos.length >= 0.5 : contenido.includes(consulta);
          });

          const coincidenciasAlimentos = (datosAlimentos.alimentos || []).map((alimento) => {
            const contenido = normalizar([
              alimento.nombre, alimento.categoria, alimento.resumen,
              'edad introduccion cuando desde que edad meses',
              'preparacion preparar ofrecer dar textura trozos pure papilla triturar aplastar',
              'seguridad seguro lavar limpiar cortar retirar semillas cascara',
              'recetas receta cocinar',
              'precauciones alergia atragantamiento riesgo evitar',
              'conservacion conservar guardar refrigerar nevera congelar',
              'beneficios beneficio bueno para que sirve',
              'propiedades nutricionales vitaminas nutrientes fibra proteina calorias grasas',
              'video youtube short',
              ...(alimento.nombres_alternativos || []),
              ...(alimento.palabras_clave || [])
            ].join(' '));
            const aciertos = terminos.filter((termino) => contenido.includes(termino)).length;
            return { alimento, puntuacion: terminos.length ? aciertos / terminos.length : (contenido.includes(consulta) ? 1 : 0) };
          }).filter((item) => item.puntuacion >= 0.5).sort((a,b) => b.puntuacion-a.puntuacion).map((item) => item.alimento);

          resultados.replaceChildren();

          if (!coincidencias.length && !coincidenciasAlimentos.length) {
            resultados.appendChild(
              elemento(
                'p',
                'ciba-global-mensaje',
                'No encontramos coincidencias. Prueba con otras palabras.'
              )
            );
            return;
          }

          coincidenciasAlimentos.slice(0, 10).forEach((alimento) => {
            const ancla = seccionSolicitada ? '--' + seccionSolicitada.clave : '';
            const rutaAlimento = alimento.ruta_publica || 'c/C1/alimentos/';
            const destino = new URL(
              rutaAlimento + '#alimento-' + encodeURIComponent(alimento.id) + ancla,
              RAIZ
            ).href;
            const resultado = enlace(
              destino,
              '',
              'ciba-global-resultado'
            );
            const nombre = elemento('strong', '', alimento.nombre || 'Alimento');
            const descripcion = elemento('small', '', alimento.resumen || 'Consultar ficha de alimento');
            const seccion = elemento(
              'small',
              'ciba-global-subseccion',
              seccionSolicitada
                ? 'Ir directamente a: ' + seccionSolicitada.etiqueta
                : 'Abrir ficha · ' + (alimento.categoria || 'Alimentación')
            );
            resultado.append(nombre, descripcion, seccion);
            resultados.appendChild(resultado);
          });

          coincidencias.slice(0, Math.max(0, 10 - coincidenciasAlimentos.length)).forEach((pagina) => {
            const resultado = enlace(
              urlPublica(pagina.ruta_publica),
              '',
              'ciba-global-resultado'
            );

            const nombre = elemento('strong', '', pagina.titulo || 'Contenido de CIBA');
            const descripcion = elemento('small', '', pagina.descripcion || 'Explorar contenido');
            resultado.append(nombre, descripcion);

            if (pagina.subseccion) {
              resultado.appendChild(
                elemento('small', 'ciba-global-subseccion', 'Sección: ' + pagina.subseccion)
              );
            }

            resultados.appendChild(resultado);
          });
        } catch (error) {
          console.error(
            'CIBA: error en el buscador.',
            error
          );

          resultados.replaceChildren(
            elemento(
              'p',
              'ciba-global-mensaje',
              'No pudimos consultar el catálogo. Inténtalo de nuevo.'
            )
          );
        }
      }
    );

    document.addEventListener('click', (evento) => {
      if (!contenedor.contains(evento.target)) {
        cerrarPanel();
      }
    });

    document.addEventListener('keydown', (evento) => {
      if (evento.key === 'Escape') cerrarPanel();
    });

    contenedor.append(boton, etiqueta, panel);
    contenedor.classList.add('ciba-oraculo-oculto');
    document.body.appendChild(contenedor);

    // El oráculo aparece cuando el contenido inicial ya está asentado.
    window.setTimeout(() => {
      if (!menuAbierto && !scrollOculto && !transicionActiva) {
        contenedor.classList.remove('ciba-oraculo-oculto');
      }
    }, 650);

    // Al navegar a otra página o artículo, se desvanece antes del cambio.
    document.addEventListener('click', (evento) => {
      const ancla = evento.target.closest('a[href]');
      if (!ancla || evento.defaultPrevented || evento.button !== 0 ||
          evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey ||
          ancla.target === '_blank') return;
      const destino = new URL(ancla.href, window.location.href);
      if (destino.origin !== window.location.origin ||
          destino.pathname === window.location.pathname) return;
      transicionActiva = true;
      actualizarVisibilidadBuscador();
    }, true);

    // Al bajar se aparta de la lectura; al subir vuelve a estar disponible.
    let ultimaPosicion = window.scrollY || 0;
    window.addEventListener('scroll', () => {
      if (menuAbierto) return;
      const panelBusqueda = document.querySelector('.ciba-global-panel-busqueda');
      if (panelBusqueda && panelBusqueda.classList.contains('abierto')) return;
      const posicion = window.scrollY || 0;
      const diferencia = posicion - ultimaPosicion;
      if (posicion < 35) {
        scrollOculto = false;
      } else if (diferencia > 8 && posicion > 90) {
        scrollOculto = true;
      } else if (diferencia < -8) {
        scrollOculto = false;
      }
      ultimaPosicion = posicion;
      actualizarVisibilidadBuscador();
    }, { passive: true });
  }

  function crearPieInstitucional() {
    if (document.querySelector('.ciba-pie-institucional')) return;

    // El pie institucional nuevo es el único pie visible en todas las páginas.
    // Retiramos los cierres antiguos que algunas páginas ya incorporaban.
    document.querySelectorAll('footer:not(.ciba-pie-institucional)').forEach((anterior) => {
      anterior.remove();
    });

    const pie = elemento('footer', 'ciba-pie-institucional');
    const identidad = elemento('p', 'ciba-pie-identidad',
      'CIBA: plataforma digital cubana de educación parental en los primeros mil días de las infancias.');
    const lema = elemento('p', 'ciba-pie-lema', 'Crecemos acompañándonos.');
    const nav = elemento('nav', 'ciba-pie-navegacion');
    nav.setAttribute('aria-label', 'Navegación principal de CIBA');
    const enlaces = [
      ['Crianza', 'c/C1/'],
      ['Internet', 'i/I1/'],
      ['Bienestar', 'b/B1/'],
      ['Acompañamiento', 'a/A1/'],
      ['Configuración de la plataforma', 'plataforma/']
    ];
    enlaces.forEach(([nombre, ruta]) => {
      nav.appendChild(enlace(urlPublica(ruta), nombre, 'ciba-pie-enlace'));
    });
    pie.append(identidad, lema, nav);
    document.body.appendChild(pie);
  }

  function iniciar() {
    cargarEstilos();
    crearPieInstitucional();
    crearMenu();
    crearBuscador();

    document.documentElement.dataset.cibaGlobal = 'listo';
  }

  if (document.readyState === 'loading') {
    document.addEventListener(
      'DOMContentLoaded',
      iniciar,
      { once: true }
    );
  } else {
    iniciar();
  }
})();
