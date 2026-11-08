// CIBA · GLOBAL
// Menú de navegación y buscador ancestral flotante.

import { CIBA } from './core/config.js';

(() => {
  'use strict';

  if (window.__CIBA_GLOBAL_INICIADO__) return;
  window.__CIBA_GLOBAL_INICIADO__ = true;

  // Raíz real del proyecto, incluso desde páginas interiores.
  const RAIZ = new URL('../../', import.meta.url);
  const RUTA_CATALOGO = new URL('data/catalogo.json', RAIZ);
  const RUTA_CSS = new URL('../css/ciba-global.css', import.meta.url);

  let catalogo = null;

  // ---------------------------------------
  // HERRAMIENTAS
  // ---------------------------------------

  function elemento(etiqueta, clase, texto) {
    const nodo = document.createElement(etiqueta);

    if (clase) nodo.className = clase;
    if (texto !== undefined) nodo.textContent = texto;

    return nodo;
  }

  function enlace(ruta, texto, clase = '') {
    const a = elemento('a', clase, texto);
    a.href = ruta;
    return a;
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

  // ---------------------------------------
  // MENÚ HAMBURGUESA
  // ---------------------------------------

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

    const titulo = elemento(
      'h2',
      'ciba-global-menu-titulo',
      'EXPLORA CIBA'
    );

    panel.appendChild(titulo);

    const inicio = enlace(
      new URL('index.html', RAIZ).href,
      'Inicio',
      'ciba-global-enlace'
    );

    panel.appendChild(inicio);

    const columnas = [
      { id: 'C', titulo: 'Crianza' },
      { id: 'I', titulo: 'Internet' },
      { id: 'B', titulo: 'Bienestar' },
      { id: 'A', titulo: 'Acompañamiento' }
    ];

    columnas.forEach((columna) => {
      const grupo = elemento('div', 'ciba-global-grupo');

      const encabezado = elemento(
        'a',
        'ciba-global-enlace'
      );

      encabezado.href = new URL('index.html#areas', RAIZ).href;

      const letra = elemento(
        'span',
        'ciba-global-letra',
        columna.id
      );

      const nombre = elemento(
        'span',
        '',
        columna.titulo
      );

      encabezado.append(letra, nombre);
      grupo.appendChild(encabezado);

      panel.appendChild(grupo);
    });

    boton.addEventListener('click', () => {
      const abierto = panel.classList.toggle('abierto');

      boton.setAttribute('aria-expanded', String(abierto));
      boton.setAttribute(
        'aria-label',
        abierto ? 'Cerrar menú de navegación' : 'Abrir menú de navegación'
      );
    });

    panel.addEventListener('click', (evento) => {
      if (evento.target.closest('a')) {
        panel.classList.remove('abierto');
        boton.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('click', (evento) => {
      if (!contenedor.contains(evento.target)) {
        panel.classList.remove('abierto');
        boton.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', (evento) => {
      if (evento.key === 'Escape') {
        panel.classList.remove('abierto');
        boton.setAttribute('aria-expanded', 'false');
      }
    });

    contenedor.append(boton, panel);
    document.body.appendChild(contenedor);

    // Completar los enlaces con las áreas publicadas.
    obtenerCatalogo()
      .then((datos) => {
        const grupos = panel.querySelectorAll(
          '.ciba-global-grupo'
        );

        columnas.forEach((columna, indice) => {
          const grupo = grupos[indice];
          const encabezado = grupo.querySelector('a');

          const areas = (datos.areas || []).filter(
            (area) => area.columna === columna.id
          );

          if (areas.length) {
            encabezado.href = urlPublica(
              areas[0].ruta_publica
            );
          }

          areas.forEach((area) => {
            const subenlace = enlace(
              urlPublica(area.ruta_publica),
              area.titulo,
              'ciba-global-enlace ciba-global-subenlace'
            );

            grupo.appendChild(subenlace);
          });
        });
      })
      .catch((error) => {
        console.warn('CIBA: no se pudieron cargar las áreas.', error);
      });
  }

  // ---------------------------------------
  // BUSCADOR ANCESTRAL
  // ---------------------------------------

  function crearBuscador() {
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
    boton.setAttribute('aria-controls', 'ciba-busqueda-panel');

    const orbita = elemento('span', 'ciba-global-orbita');

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
    panel.setAttribute('aria-label', 'Buscador de CIBA');

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
    cerrar.setAttribute('aria-label', 'Cerrar buscador');

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
    entrada.setAttribute('aria-label', 'Buscar en CIBA');
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

      setTimeout(() => entrada.focus(), 100);
    }

    boton.addEventListener('click', () => {
      if (panel.classList.contains('abierto')) {
        cerrarPanel();
      } else {
        abrirPanel();
      }
    });

    cerrar.addEventListener('click', cerrarPanel);

    formulario.addEventListener('submit', async (evento) => {
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
        console.error('CIBA: error en el buscador.', error);

        resultados.replaceChildren(
          elemento(
            'p',
            'ciba-global-mensaje',
            'No pudimos consultar el catálogo. Inténtalo de nuevo.'
          )
        );
      }
    });

    document.addEventListener('click', (evento) => {
      if (!contenedor.contains(evento.target)) {
        cerrarPanel();
      }
    });

    document.addEventListener('keydown', (evento) => {
      if (evento.key === 'Escape') {
        cerrarPanel();
      }
    });

    contenedor.append(boton, etiqueta, panel);
    document.body.appendChild(contenedor);
  }

  // ---------------------------------------
  // INICIO
  // ---------------------------------------

  function iniciar() {
    cargarEstilos();
    crearMenu();
    crearBuscador();

    document.documentElement.dataset.cibaGlobal = 'listo';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar, {
      once: true
    });
  } else {
    iniciar();
  }

})();