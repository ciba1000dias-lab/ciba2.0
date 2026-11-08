
// CIBA · SISTEMA GLOBAL
// Navegación principal y buscador ancestral.

(() => {
  'use strict';

  if (window.__CIBA_GLOBAL_INICIADO__) return;
  window.__CIBA_GLOBAL_INICIADO__ = true;

  const RAIZ = new URL('../../', import.meta.url);
  const RUTA_CATALOGO = new URL('data/catalogo.json', RAIZ);
  const RUTA_CSS = new URL('../css/ciba-global.css', import.meta.url);

  let catalogo = null;

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

  function cerrarMenu(panel, boton) {
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

  function crearMenu() {
    if (document.querySelector('.ciba-global-menu')) return;

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

    // SOBRE EL PROYECTO
    crearSubmenu(
      'Sobre el proyecto',
      ['Desarrolladores del proyecto'],
      panel
    );

    // CONFIGURACIÓN
    crearSubmenu(
      'Configuración',
      ['Licencia Creative Commons'],
      panel
    );

    boton.addEventListener('click', () => {
      const abierto = panel.classList.toggle('abierto');

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
    document.body.appendChild(contenedor);

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

        resultados.replaceChildren(
          elemento(
            'p',
            'ciba-global-mensaje',
            'Consultando el conocimiento de CIBA...'
          )
        );

        try {
          const datos = await obtenerCatalogo();
          const paginas = datos.paginas || [];

          const coincidencias = paginas.filter((pagina) => {
            const contenido = normalizar([
              pagina.titulo,
              pagina.descripcion,
              pagina.id,
              pagina.area,
              ...(pagina.palabras_clave || [])
            ].join(' '));

            return contenido.includes(consulta);
          });

          resultados.replaceChildren();

          if (!coincidencias.length) {
            resultados.appendChild(
              elemento(
                'p',
                'ciba-global-mensaje',
                'No encontramos coincidencias. Prueba con otras palabras.'
              )
            );
            return;
          }

          coincidencias.slice(0, 10).forEach((pagina) => {
            const resultado = enlace(
              urlPublica(pagina.ruta_publica),
              '',
              'ciba-global-resultado'
            );

            const nombre = elemento(
              'strong',
              '',
              pagina.titulo || 'Contenido de CIBA'
            );

            const descripcion = elemento(
              'small',
              '',
              pagina.descripcion || 'Explorar contenido'
            );

            resultado.append(nombre, descripcion);
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
    document.body.appendChild(contenedor);
  }

  function iniciar() {
    cargarEstilos();
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
