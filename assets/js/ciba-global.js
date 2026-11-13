
// CIBA · SISTEMA GLOBAL
// Navegación principal y buscador ancestral.

(() => {
  'use strict';

  if (window.__CIBA_GLOBAL_INICIADO__) return;
  window.__CIBA_GLOBAL_INICIADO__ = true;

  const RAIZ = new URL('../../', import.meta.url);
  const RUTA_CATALOGO = new URL('data/catalogo.json', RAIZ);
  const RUTA_ALIMENTOS = new URL('assets/data/alimentos-busqueda.json', RAIZ);
  const RUTA_CSS = new URL('../css/ciba-global.css?v=20261112-08', import.meta.url);

  let catalogo = null;
  let alimentos = null;
  let menuAbierto = false;
  let transicionActiva = false;

  function actualizarVisibilidadBuscador() {
    const buscador = document.querySelector('.ciba-global-buscador');
    if (!buscador) return;
    // El Oráculo permanece visible incluso cuando se despliega el menú.
    buscador.classList.remove('ciba-oraculo-oculto');
  }

  const columnas = [
    { id: 'C', titulo: 'Crianza' },
    { id: 'I', titulo: 'INTERNET' },
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

  let secuenciaSubmenusPreparacion = 0;

  function crearSubmenu(titulo, opciones, panel) {
    const grupo = elemento('div', 'ciba-global-grupo');
    const lista = elemento('div', 'ciba-global-submenu');
    lista.id = 'ciba-submenu-preparacion-' + (++secuenciaSubmenusPreparacion);
    lista.hidden = true;

    const encabezado = elemento(
      'button',
      'ciba-global-enlace ciba-global-submenu-toggle',
      titulo
    );

    encabezado.type = 'button';
    encabezado.setAttribute('aria-controls', lista.id);
    encabezado.setAttribute('aria-expanded', 'false');

    encabezado.addEventListener('click', () => {
      const abrir = lista.hidden;
      lista.hidden = !abrir;
      encabezado.setAttribute('aria-expanded', String(abrir));
    });

    opciones.forEach((opcion) => {
      const item = elemento(
        'span',
        'ciba-global-enlace ciba-global-subenlace',
        opcion
      );

      item.setAttribute('aria-disabled', 'true');
      item.title = 'Apartado en preparación';
      lista.appendChild(item);
    });

    grupo.append(encabezado, lista);
    panel.appendChild(grupo);
  }

  function resolverColumnaActual() {
    const ruta = window.location.pathname;
    const relativa = ruta.startsWith(RAIZ.pathname) ? ruta.slice(RAIZ.pathname.length) : ruta.replace(/^\/+/, '');
    const prefijo = relativa.match(/^([ciba])(?:\/|$)/i);
    let id = prefijo ? prefijo[1].toUpperCase() : '';
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

    // Retirar las antiguas barras de marca para que el menú global sea la única cabecera de navegación.
    document.querySelectorAll('header.cabecera, header.top, header.cab, header.plataforma-top').forEach((anterior) => {
      anterior.remove();
    });
    // Algunas páginas auxiliares usan un header sin clase para mostrar solo el logotipo.
    document.querySelectorAll('header:not(.hero):not(.cabecera-articulo)').forEach((anterior) => {
      if (anterior.querySelector('a.marca')) anterior.remove();
    });

    const actual = resolverColumnaActual();
    const colores = { C:'#397653', I:'#287B9A', B:'#8C671F', A:'#A9443B' };
    if (actual.id) document.body.dataset.cibaColumna = actual.id.toLowerCase();
    if (/\/c\/C2(?:\/|$)/i.test(window.location.pathname) && document.querySelector('.ciba-articulo')) document.body.classList.add('ciba-area-sueno-descanso');
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

    // ACCESO GENERAL
    panel.appendChild(enlace(new URL('index.html', RAIZ).href,'Inicio CIBA','ciba-global-enlace'));

    const tituloColumnas = elemento('h2','ciba-global-menu-titulo ciba-global-menu-separador','LAS CUATRO COLUMNAS');
    panel.appendChild(tituloColumnas);

    let secuenciaSubmenus = 0;

    function crearDesplegable(titulo, clase='', ruta=null) {
      const grupo=elemento('div','ciba-global-grupo '+clase);
      const lista=elemento('div','ciba-global-submenu');
      lista.id = 'ciba-submenu-' + (++secuenciaSubmenus);
      lista.hidden=true;

      let botonGrupo;
      if(ruta) {
        const cabecera=elemento('div','ciba-global-cabecera-grupo');
        botonGrupo=enlace(urlPublica(ruta),titulo,'ciba-global-enlace ciba-global-enlace-directo');
        const control=elemento('button','ciba-global-enlace ciba-global-desplegable ciba-global-desplegable-control');
        control.type='button';
        control.setAttribute('aria-label','Mostrar u ocultar '+titulo);
        control.setAttribute('aria-controls', lista.id);
        control.setAttribute('aria-expanded','false');
        control.addEventListener('click',()=>{
          const abrir=lista.hidden;
          if(abrir){
            Array.from(grupo.parentElement.children).forEach(hermano=>{
              if(hermano===grupo || !hermano.classList.contains('ciba-global-grupo')) return;
              const submenu=Array.from(hermano.children).find(hijo=>hijo.classList.contains('ciba-global-submenu'));
              const controlHermano=hermano.querySelector(':scope > .ciba-global-cabecera-grupo > .ciba-global-desplegable-control, :scope > .ciba-global-desplegable');
              if(submenu && controlHermano){
                submenu.hidden=true;
                controlHermano.setAttribute('aria-expanded','false');
                hermano.classList.remove('desplegado');
              }
            });
          }
          lista.hidden=!abrir;
          control.setAttribute('aria-expanded',String(abrir));
          grupo.classList.toggle('desplegado',abrir);
        });
        cabecera.append(botonGrupo,control);
        grupo.append(cabecera,lista);
      } else {
        botonGrupo=elemento('button','ciba-global-enlace ciba-global-desplegable',titulo);
        botonGrupo.type='button';
        botonGrupo.setAttribute('aria-controls', lista.id);
        botonGrupo.setAttribute('aria-expanded','false');
        botonGrupo.addEventListener('click',()=>{
          const abrir=lista.hidden;
          if(abrir){
            Array.from(grupo.parentElement.children).forEach(hermano=>{
              if(hermano===grupo || !hermano.classList.contains('ciba-global-grupo')) return;
              const submenu=Array.from(hermano.children).find(hijo=>hijo.classList.contains('ciba-global-submenu'));
              const controlHermano=hermano.querySelector(':scope > .ciba-global-cabecera-grupo > .ciba-global-desplegable-control, :scope > .ciba-global-desplegable');
              if(submenu && controlHermano){
                submenu.hidden=true;
                controlHermano.setAttribute('aria-expanded','false');
                hermano.classList.remove('desplegado');
              }
            });
          }
          lista.hidden=!abrir;
          botonGrupo.setAttribute('aria-expanded',String(abrir));
          grupo.classList.toggle('desplegado',abrir);
        });
        grupo.append(botonGrupo,lista);
      }
      return {grupo,botonGrupo,lista};
    }

    function agregarEnlace(lista,ruta,titulo,clase='ciba-global-enlace ciba-global-subenlace') {
      if(!ruta) return;
      lista.appendChild(enlace(urlPublica(ruta),titulo,clase));
    }

    async function agregarApartadosDeSeccionInternet(lista, area) {
      const ruta = 'i/' + area.id + '/';
      try {
        const respuesta = await fetch(urlPublica(ruta), { cache: 'no-cache' });
        if (!respuesta.ok) throw new Error('No se pudo cargar ' + ruta);
        const html = await respuesta.text();
        const documento = new DOMParser().parseFromString(html, 'text/html');
        const apartados = Array.from(documento.querySelectorAll('section.block[id]'))
          .map(seccion => ({
            id: seccion.id,
            titulo: seccion.querySelector('h2')?.textContent?.trim() || ''
          }))
          .filter(apartado => apartado.id && apartado.titulo);

        if (!apartados.length) {
          agregarEnlace(lista, ruta, 'Abrir sección completa');
          return;
        }

        apartados.forEach(apartado => {
          agregarEnlace(lista, ruta + '#' + encodeURIComponent(apartado.id), apartado.titulo);
        });
      } catch (error) {
        console.warn('CIBA: no se pudieron cargar los apartados de ' + area.id, error);
        agregarEnlace(lista, ruta, 'Abrir sección completa');
      }
    }

    async function construirNavegacionEditorial() {
      const datos = await obtenerCatalogo();

      // Taxonomía oficial: 23 áreas hermanas distribuidas en cuatro columnas.
      // Alimentación y Lactancia comparten la carpeta fuente C1, pero tienen
      // portadas y rutas públicas independientes.
      const taxonomia = {
        C: [
          { id:'C1-ALIMENTACION', fuente:'C1', titulo:'Alimentación', ruta:'c/C1/alimentacion/' },
          { id:'C1-LACTANCIA', fuente:'C1', titulo:'Lactancia', ruta:'c/C1/lactancia/' },
          { id:'C2', titulo:'Sueño y descanso' },
          { id:'C3', titulo:'Cuidados básicos y autonomía' },
          { id:'C4', titulo:'Juego, estimulación y aprendizaje' },
          { id:'C5', titulo:'Vínculo, apego y desarrollo socioemocional' },
          { id:'C6', titulo:'Prevención y seguridad en el hogar' },
          { id:'C7', titulo:'Cultura, rutinas y vida cotidiana' }
        ],
        I: [
          { id:'I1', titulo:'Alfabetización sanitaria digital', ruta:'i/I1/' },
          { id:'I2', titulo:'Desinformación y consejos virales', ruta:'i/I2/' },
          { id:'I3', titulo:'Privacidad y seguridad infantil en redes', ruta:'i/I3/' },
          { id:'I4', titulo:'Pantallas y desarrollo', ruta:'i/I4/' },
          { id:'I5', titulo:'Inteligencia artificial e infancias', ruta:'i/I5/' },
          { id:'I6', titulo:'Redes sociales y salud mental familiar', ruta:'i/I6/' },
          { id:'I7', titulo:'Apps, plataformas y herramientas digitales', ruta:'i/I7/' },
          { id:'I8', titulo:'Telemedicina y comunicación digital con el sistema de salud', ruta:'i/I8/' },
          { id:'I9', titulo:'Contenido infantil y consumo audiovisual', ruta:'i/I9/' },
          { id:'I10', titulo:'Ciudadanía digital y futuro', ruta:'i/I10/' }
        ],
        B: [
          { id:'B1', titulo:'Salud del bebé', ruta:'b/#tema-01' },
          { id:'B2', titulo:'Salud materna y posparto', ruta:'b/#tema-02' },
          { id:'B3', titulo:'Salud emocional perinatal', ruta:'b/#tema-03' },
          { id:'B4', titulo:'Nutrición y estado nutricional', ruta:'b/#tema-04' },
          { id:'B5', titulo:'Prevención clínica y vacunas', ruta:'b/#tema-05' },
          { id:'B6', titulo:'Crecimiento y desarrollo', ruta:'b/#tema-06' },
          { id:'B7', titulo:'Enfermedades frecuentes en la primera infancia', ruta:'b/#tema-07' },
          { id:'B8', titulo:'Señales de alarma y urgencias', ruta:'b/#tema-08' },
          { id:'B9', titulo:'Salud bucal y hábitos saludables', ruta:'b/#tema-09' },
          { id:'B10', titulo:'Salud ambiental y prevención de riesgos clínicos', ruta:'b/#tema-10' }
        ],
        A: [
          { id:'A1', titulo:'Apoyo emocional a la familia', ruta:'a/#tema-01' },
          { id:'A2', titulo:'Corresponsabilidad y familia', ruta:'a/#tema-02' },
          { id:'A3', titulo:'Redes de apoyo y comunidad', ruta:'a/#tema-03' },
          { id:'A4', titulo:'Cuidado del cuidador', ruta:'a/#tema-04' },
          { id:'A5', titulo:'Acompañamiento práctico y seguimiento', ruta:'a/#tema-05' },
          { id:'A6', titulo:'Crianza a distancia y migración', ruta:'a/#tema-06' },
          { id:'A7', titulo:'Abuelos y cuidadores', ruta:'a/#tema-07' },
          { id:'A8', titulo:'Familias diversas y situaciones especiales', ruta:'a/#tema-08' },
          { id:'A9', titulo:'Duelo, pérdida y situaciones difíciles', ruta:'a/#tema-09' },
          { id:'A10', titulo:'Comunidad CIBA y acompañamiento entre familias', ruta:'a/#tema-10' }
        ]
      };

      // Corrige la ubicación de tres contenidos heredados de la clasificación
      // inicial: desarrollo infantil, sueño y la serie de lactancia.
      function resolverAreaEditorial(pagina) {
        const id = String(pagina.id || '');
        if (id === 'C1-01') return 'C4';
        if (id === 'C1-03') return 'C2';
        if (/^C1-(?:1[6-9]|[2-3]\d|40)$/.test(id)) return 'C1-LACTANCIA';
        // El catálogo conserva C1 como área fuente compartida.
        // Los demás contenidos se indexan bajo el área hermana Alimentación.
        if (pagina.columna === 'C' && pagina.area === 'C1') return 'C1-ALIMENTACION';
        return pagina.area;
      }

      function ordenarPaginas(a, b) {
        const numeroA = Number((String(a.id || '').match(/-(\d+)$/) || [])[1] || 0);
        const numeroB = Number((String(b.id || '').match(/-(\d+)$/) || [])[1] || 0);
        if (numeroA && numeroB && numeroA !== numeroB) return numeroA - numeroB;
        return String(a.titulo || '').localeCompare(String(b.titulo || ''), 'es');
      }

      function agregarPaginasDeArea(lista, paginas) {
        const grupos = new Map();
        paginas.forEach(pagina => {
          const nombre = pagina.subseccion || 'Contenidos generales';
          if (!grupos.has(nombre)) grupos.set(nombre, []);
          grupos.get(nombre).push(pagina);
        });

        grupos.forEach((items, nombre) => {
          if (grupos.size > 1) {
            const subgrupo = crearDesplegable(nombre, 'ciba-global-subarea');
            items.forEach(pagina => {
              agregarEnlace(subgrupo.lista, pagina.ruta_publica, pagina.titulo);
            });
            lista.appendChild(subgrupo.grupo);
          } else {
            items.forEach(pagina => {
              agregarEnlace(lista, pagina.ruta_publica, pagina.titulo);
            });
          }
        });
      }

      // RECURSOS DESTACADOS: accesos transversales disponibles desde cualquier página.
      const tituloRecursos = elemento('h2','ciba-global-menu-titulo ciba-global-menu-separador','RECURSOS DESTACADOS');
      const grupoRecursos = crearDesplegable('Herramientas y espacios útiles','ciba-global-recursos');
      [
        ['c/C1/alimentos/','Biblioteca de alimentos'],
        ['c/C1/recetario/','¿Qué cocino hoy?'],
        ['c/C1/fonoteca/','Fonoteca infantil'],
        ['plataforma/recursos/descargables/','Recursos descargables'],
        ['plataforma/comunidad/','Comunidad CIBA'],
        ['c/C1/podcast/','Zona Podcast'],
        ['c/C6/','Prevención y seguridad en el hogar'],
        ['i/I7/','Apps, plataformas y herramientas digitales'],
        ['i/I7/#apps-10','Las 10 apps que no te pueden faltar']
      ].forEach(([ruta,titulo]) => agregarEnlace(grupoRecursos.lista,ruta,titulo));
      panel.insertBefore(tituloRecursos,tituloColumnas);
      panel.insertBefore(grupoRecursos.grupo,tituloColumnas);

      columnas.forEach(columna => {
        const areasFuente = (datos.areas || []).filter(area => area.columna === columna.id);
        const areasColumna = taxonomia[columna.id] || [];
        const rutaColumna = ({ I:'i/', B:'b/', A:'a/' })[columna.id] || (areasFuente.sort((a, b) => (a.orden || 0) - (b.orden || 0))[0]?.ruta_publica || null);
        const grupoColumna = crearDesplegable(
          columna.titulo,
          'ciba-global-columna ciba-global-columna-' + columna.id.toLowerCase(),
          rutaColumna
        );

        const letra = elemento('span', 'ciba-global-letra', columna.id);
        grupoColumna.botonGrupo.prepend(letra);

        areasColumna.forEach(areaMenu => {
          const areaFuente = areasFuente.find(area => area.id === (areaMenu.fuente || areaMenu.id));
          const rutaArea = areaMenu.ruta || areaFuente?.ruta_publica ||
            (columna.id.toLowerCase() + '/' + (areaMenu.fuente || areaMenu.id) + '/');

          // Todas las áreas usan exactamente el mismo componente:
          // enlace directo a la portada + control independiente para desplegar.
          const grupoArea = crearDesplegable(
            areaMenu.titulo,
            'ciba-global-area',
            rutaArea
          );

          const paginas = (datos.paginas || [])
            .filter(pagina =>
              pagina.columna === columna.id &&
              resolverAreaEditorial(pagina) === areaMenu.id &&
              pagina.mostrar_en_area !== false
            )
            .sort(ordenarPaginas);

          if (columna.id === 'I') {
            await agregarApartadosDeSeccionInternet(grupoArea.lista, areaMenu);
          } else {
            agregarPaginasDeArea(grupoArea.lista, paginas);
          }
          grupoColumna.lista.appendChild(grupoArea.grupo);
        });

        panel.insertBefore(grupoColumna.grupo, tituloPlataforma);
      });
    }

    const seccionesPlataforma = [
      ["sobre-ciba","Sobre CIBA",[["mision-y-lema","Misión y lema"],["nuestro-equipo","Nuestro equipo"],["declaracion-editorial","Declaración editorial"]]],
      ["confianza-y-legal","Confianza y legal",[["aviso-medico","Aviso médico"],["privacidad","Privacidad"],["datos-de-menores","Datos de menores"],["terminos-de-uso","Términos de uso"],["como-citar","Cómo citar"]]],
      ["configuracion","Configuración",[]],
      ["navegacion","Navegación",[["buscar","Buscar"],["indice-tematico","Índice temático"],["recorrido-por-edad","Recorrido por edad"],["series","Series"],["glosario","Glosario"]]],
      ["comunidad","Comunidad",[["preguntale-al-pediatra","Pregúntale al pediatra"],["reportar-error","Reportar un error"],["compartir","Compartir"],["unirse-al-equipo","Unirse al equipo"]]],
      ["recursos","Recursos",[["descargables","Descargables"],["multimedia","Multimedia"],["enlaces-recomendados","Enlaces recomendados"],["redes-sociales","Nuestras redes"]]]
    ];

    const tituloPlataforma=elemento('h2','ciba-global-menu-titulo ciba-global-menu-separador','PLATAFORMA');
    panel.appendChild(tituloPlataforma);
    const grupoPlataforma=crearDesplegable('Plataforma','ciba-global-plataforma','plataforma/');
    seccionesPlataforma.forEach(seccion=>{
      const grupo=crearDesplegable(seccion[1],'ciba-global-area','plataforma/'+seccion[0]+'/');
      seccion[2].forEach(apartado=>agregarEnlace(grupo.lista,'plataforma/'+seccion[0]+'/'+apartado[0]+'/',apartado[1]));
      grupoPlataforma.lista.appendChild(grupo.grupo);
    });
    panel.appendChild(grupoPlataforma.grupo);

    // Herramienta transversal: buscador
    const buscar=elemento('button','ciba-global-enlace ciba-global-herramienta','BUSCADOR CIBA');
    buscar.type='button';
    buscar.addEventListener('click',()=>{
      cerrarMenu(panel,boton);
      const oraculo=document.querySelector('.ciba-global-oraculo');
      if(oraculo) oraculo.click();
      else if(esPortada()) abrirBuscadorDePortada();
    });
    panel.appendChild(buscar);

    construirNavegacionEditorial().catch(error=>console.warn('CIBA: no se pudo construir el índice jerárquico del menú.',error));

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
      if (!contenedor.contains(evento.target) && !panel.contains(evento.target)) {
        cerrarMenu(panel, boton);
      }
    });

    document.addEventListener('keydown', (evento) => {
      if (evento.key === 'Escape' && panel.classList.contains('abierto')) {
        cerrarMenu(panel, boton);
        boton.focus();
      }
    });

    contenedor.appendChild(boton);
    // Portal global: el botón y el panel viven directamente en body para
    // escapar de stacking contexts creados por cabeceras, heroes o micrositios.
    // Así la navegación conserva prioridad visual en todas las columnas.
    document.body.appendChild(contenedor);
    document.body.appendChild(panel);


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
    // El oráculo flotante está disponible en portada y páginas interiores.
    // La portada conserva además su buscador integrado como vía alternativa.
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
    entrada.placeholder = 'Ej.: boniato, cólicos, gripe, mocos';
    entrada.setAttribute(
      'aria-label',
      'Buscar en CIBA por palabras clave'
    );
    entrada.setAttribute('aria-describedby', 'ciba-oraculo-ayuda');
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

    const ayuda = elemento(
      'p',
      'ciba-global-busqueda-ayuda',
      'Este es un buscador simple por palabras clave. Escribe solo una o varias palabras; no redactes una oración ni una pregunta.'
    );
    ayuda.id = 'ciba-oraculo-ayuda';
    const ejemplos = elemento(
      'p',
      'ciba-global-busqueda-ejemplos',
      'Ejemplos: Boniato · cólicos · gripe · mocos'
    );

    panel.append(cabecera, ayuda, ejemplos, formulario, resultados);

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
          // Entrada de área para que Oráculo encuentre la sección incluso antes
          // de publicar sus diez guías individuales.
          const paginasConAreas = [...paginas, {
            id: 'C6',
            titulo: 'Prevención y seguridad en el hogar',
            descripcion: 'Guía de CIBA para prevenir accidentes domésticos y responder ante riesgos durante los primeros dos años: sueño seguro, atragantamiento, ahogamiento, quemaduras, caídas, electricidad, intoxicaciones, objetos pequeños, humo, monóxido y plan familiar de emergencia.',
            columna: 'C',
            area: 'C6',
            subseccion: 'Prevención y seguridad en el hogar',
            palabras_clave: ['prevencion', 'seguridad', 'accidentes', 'hogar', 'casa', 'riesgos', 'sueño seguro', 'muerte subita', 'atragantamiento', 'asfixia', 'ahogamiento', 'baño seguro', 'quemaduras', 'caidas', 'golpes', 'enchufes', 'electricidad', 'intoxicaciones', 'productos de limpieza', 'medicamentos', 'plantas toxicas', 'objetos pequeños', 'pilas', 'imanes', 'humo', 'monoxido de carbono', 'ventilacion', 'botiquin', 'emergencia', 'primeros auxilios', 'lactante', 'bebe'],
            ruta_publica: 'c/C6/'
          }];

          // Buscar tanto artículos como fichas de la biblioteca de alimentos.
          const coincidencias = paginasConAreas.filter((pagina) => {
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
      if (!menuAbierto && !transicionActiva) {
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

    // El Oráculo permanece disponible durante toda la lectura.
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
      ['INTERNET', 'i/'],
      ['Bienestar', 'b/B1/'],
      ['Acompañamiento', 'a/A1/'],
      ['Configuración de la plataforma', 'plataforma/configuracion/']
    ];
    enlaces.forEach(([nombre, ruta]) => {
      nav.appendChild(enlace(urlPublica(ruta), nombre, 'ciba-pie-enlace'));
    });
    pie.append(identidad, lema, nav);
    document.body.appendChild(pie);
  }


  const CLAVE_PREFERENCIAS = 'ciba-preferencias-lectura-v1';
  const PREFERENCIAS_BASE = {
    texto: '100',
    contraste: 'normal',
    espacio: 'normal',
    ancho: 'normal',
    movimiento: 'normal',
    tema: 'claro'
  };

  function leerPreferencias() {
    try {
      const guardadas = JSON.parse(localStorage.getItem(CLAVE_PREFERENCIAS) || '{}');
      return { ...PREFERENCIAS_BASE, ...guardadas };
    } catch (_) {
      return { ...PREFERENCIAS_BASE };
    }
  }

  function aplicarPreferencias(preferencias = leerPreferencias()) {
    const html = document.documentElement;
    html.dataset.cibaContraste = preferencias.contraste;
    html.dataset.cibaEspacio = preferencias.espacio;
    html.dataset.cibaAncho = preferencias.ancho;
    html.dataset.cibaMovimiento = preferencias.movimiento;
    html.dataset.cibaTema = preferencias.tema || 'claro';
    html.style.fontSize = (16 * Number(preferencias.texto || 100) / 100) + 'px';
    try {
      localStorage.setItem(CLAVE_PREFERENCIAS, JSON.stringify(preferencias));
    } catch (_) {}
    document.querySelectorAll('[data-ciba-setting]').forEach((control) => {
      const clave = control.dataset.cibaSetting;
      const valor = preferencias[clave] || PREFERENCIAS_BASE[clave];
      control.setAttribute('aria-pressed', String(control.dataset.value === valor));
      control.classList.toggle('activo', control.dataset.value === valor);
    });
    document.querySelectorAll('[data-ciba-current]').forEach((nodo) => {
      const clave = nodo.dataset.cibaCurrent;
      const valor = preferencias[clave] || PREFERENCIAS_BASE[clave];
      const etiquetas = {
        texto: { '90':'Pequeña', '100':'Estándar', '110':'Grande', '120':'Muy grande' },
        contraste: { normal:'Estándar', alto:'Alto' },
        espacio: { normal:'Estándar', amplio:'Ampliado' },
        ancho: { normal:'Estándar', amplio:'Amplio' },
        movimiento: { normal:'Habitual', reducido:'Reducido' },
        tema: { claro:'Claro', oscuro:'Oscuro' }
      };
      nodo.textContent = (etiquetas[clave] && etiquetas[clave][valor]) || valor;
    });
  }

  function iniciarPreferencias() {
    aplicarPreferencias();
    document.addEventListener('click', (evento) => {
      const control = evento.target.closest('[data-ciba-setting]');
      if (control) {
        const preferencias = leerPreferencias();
        preferencias[control.dataset.cibaSetting] = control.dataset.value;
        aplicarPreferencias(preferencias);
        return;
      }
      const restablecer = evento.target.closest('[data-ciba-reset]');
      if (restablecer) aplicarPreferencias({ ...PREFERENCIAS_BASE });
    });
  }


  // Microinteracciones ligeras para la iconografía de toda la plataforma.
  // No descarga bibliotecas ni imágenes externas; también cubre componentes dinámicos.
  function activarMicrointeraccionesIconos() {
    const selector = [
      '[class*="icon"]', '[class*="Icon"]', '[class*="ico"]',
      '[class*="simbolo"]', '[class*="espiral"]', '[class*="oraculo"]',
      '[class^="fa-"]', '[class*=" fa-"]', '.fa', '.fas', '.far', '.fab',
      '[class^="bi-"]', '[class*=" bi-"]',
      '[class^="lucide"]', '[class*=" lucide"]', '[data-lucide]',
      '.material-icons', '.material-symbols-outlined',
      '.estado-icono', '.equipo-avatar-sello', '.ciba-info',
      '.ciba-columna-acceso .letra', '.ciba-global-letra',
      'i[class]', '.plataforma-estado i',
      'svg', 'span[aria-hidden="true"]', 'i[aria-hidden="true"]'
    ].join(',');

    const marcar = (raiz) => {
      if (!raiz || raiz.nodeType !== 1) return;
      if (raiz.matches(selector)) raiz.classList.add('ciba-icono-vivo');
      raiz.querySelectorAll(selector).forEach((nodo) => {
        nodo.classList.add('ciba-icono-vivo');
      });
    };

    marcar(document.body);
    const observador = new MutationObserver((cambios) => {
      cambios.forEach((cambio) => {
        cambio.addedNodes.forEach((nodo) => marcar(nodo));
      });
    });
    observador.observe(document.body, { childList: true, subtree: true });
  }


  // Vectores editoriales SVG: aparecen al entrar en pantalla, también en móvil.
  // Se insertan solo en aperturas de sección y párrafos introductorios para evitar ruido.
  function activarVectoresDeLectura() {
    const articulos = document.querySelectorAll('.ciba-articulo');
    if (!articulos.length) return;

    const NS = 'http://www.w3.org/2000/svg';
    const motivos = [
      {
        clase: 'hoja',
        trazos: [
          ['path', 'M8 37 C8 17 22 7 39 8 C39 25 29 39 8 37 Z'],
          ['path', 'M9 37 C17 27 25 20 37 10'],
          ['path', 'M20 27 C19 20 15 17 11 15']
        ]
      },
      {
        clase: 'espiral',
        trazos: [
          ['path', 'M24 24 C24 16 36 16 36 25 C36 39 14 40 10 25 C5 5 35 1 43 18'],
          ['path', 'M24 24 C27 21 30 24 28 27 C26 30 21 28 21 24']
        ]
      },
      {
        clase: 'vinculo',
        trazos: [
          ['path', 'M8 25 C8 14 17 8 25 14 C32 19 31 29 24 34'],
          ['path', 'M40 23 C40 34 31 40 23 34 C16 29 17 19 24 14'],
          ['path', 'M17 24 L31 24']
        ]
      }
    ];

    function crearVector(indice, tipo) {
      const motivo = motivos[indice % motivos.length];
      const marca = document.createElement('span');
      marca.className = 'ciba-vector-lectura ciba-vector-' + motivo.clase + ' ciba-vector-' + tipo;
      marca.setAttribute('aria-hidden', 'true');
      const svg = document.createElementNS(NS, 'svg');
      svg.setAttribute('viewBox', '0 0 48 48');
      svg.setAttribute('focusable', 'false');
      motivo.trazos.forEach(([etiqueta, d]) => {
        const trazo = document.createElementNS(NS, etiqueta);
        trazo.setAttribute('d', d);
        trazo.setAttribute('class', 'ciba-vector-trazo');
        svg.appendChild(trazo);
      });
      marca.appendChild(svg);
      return marca;
    }

    let indice = 0;
    const observados = [];
    articulos.forEach((articulo) => {
      const cabecera = articulo.querySelector('.cabecera-articulo');
      const primerParrafo = cabecera && cabecera.nextElementSibling;
      if (primerParrafo && primerParrafo.matches('p') && !primerParrafo.querySelector('.ciba-vector-lectura')) {
        primerParrafo.prepend(crearVector(indice++, 'parrafo'));
        observados.push(primerParrafo.querySelector('.ciba-vector-lectura'));
      }

      articulo.querySelectorAll('h2, h3').forEach((titulo) => {
        if (titulo.querySelector('.ciba-vector-lectura')) return;
        titulo.prepend(crearVector(indice++, 'titulo'));
        observados.push(titulo.querySelector('.ciba-vector-lectura'));

        const siguiente = titulo.nextElementSibling;
        if (siguiente && siguiente.matches('p') && !siguiente.querySelector('.ciba-vector-lectura')) {
          siguiente.prepend(crearVector(indice++, 'parrafo'));
          observados.push(siguiente.querySelector('.ciba-vector-lectura'));
        }
      });
    });

    if (!observados.length) return;
    const movimientoReducido = window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
      document.documentElement.dataset.cibaMovimiento === 'reducido';

    if (movimientoReducido || !('IntersectionObserver' in window)) {
      observados.forEach((marca) => marca.classList.add('ciba-vector-visible'));
      return;
    }

    const observador = new IntersectionObserver((entradas) => {
      entradas.forEach((entrada) => {
        if (!entrada.isIntersecting) return;
        entrada.target.classList.add('ciba-vector-visible');
        observador.unobserve(entrada.target);
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -6% 0px' });

    observados.forEach((marca) => observador.observe(marca));
  }

  function iniciar() {
    iniciarPreferencias();
    activarMicrointeraccionesIconos();
    activarVectoresDeLectura();
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
