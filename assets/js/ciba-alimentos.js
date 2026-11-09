// CIBA · BIBLIOTECA DE ALIMENTOS
// Renderizado seguro desde assets/data/alimentos.json.

(() => {
  'use strict';

  const raiz = new URL('../../', import.meta.url);
  const rutaIndice = new URL('assets/data/alimentos.json', raiz);

  const normalizar = (valor) => String(valor || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

  function resolverSeccion(consulta) {
    const q = normalizar(consulta);
    const reglas = [
      { clave: 'edad', patrones: ['edad', 'desde cuando', 'a partir de cuando', 'cuando introducir', 'cuando puedo', 'meses puede', 'a que edad'] },
      { clave: 'preparacion', patrones: ['preparar', 'preparacion', 'como dar', 'como ofrecer', 'textura', 'trozos', 'pure', 'papilla', 'aplastar', 'triturar', 'cortar para'] },
      { clave: 'seguridad', patrones: ['seguro', 'segura', 'lavar', 'limpiar', 'cascara', 'semillas', 'hueso', 'atragantamiento'] },
      { clave: 'precauciones', patrones: ['precaucion', 'precauciones', 'alergia', 'alergico', 'riesgo', 'peligro', 'evitar', 'contraindicacion'] },
      { clave: 'recetas', patrones: ['receta', 'recetas', 'cocinar', 'que puedo hacer', 'que puedo preparar'] },
      { clave: 'conservacion', patrones: ['conservar', 'conservacion', 'guardar', 'nevera', 'refrigerar', 'cuanto dura', 'congelar', 'almacenar'] },
      { clave: 'beneficios', patrones: ['beneficio', 'beneficios', 'para que sirve', 'es bueno', 'bueno para'] },
      { clave: 'propiedades', patrones: ['propiedad', 'propiedades', 'vitamina', 'vitaminas', 'nutriente', 'nutrientes', 'fibra', 'proteina', 'calorias', 'grasa', 'composicion', 'nutricional'] },
      { clave: 'fuentes', patrones: ['fuente', 'fuentes', 'referencia', 'referencias', 'bibliografia', 'evidencia'] },
      { clave: 'video', patrones: ['video', 'youtube', 'short'] },
      { clave: 'descripcion', patrones: ['que es', 'informacion general', 'descripcion', 'describe'] }
    ];
    return reglas.find((regla) => regla.patrones.some((patron) => q.includes(patron))) || null;
  }

  function urlImagenOptimizada(original, ancho) {
    if (!original) return '';
    try {
      const url = new URL(original);
      const esWikimedia = /(^|\.)wikimedia\.org$/i.test(url.hostname);
      if (!esWikimedia) return original;

      if (url.pathname.includes('/wiki/Special:FilePath/')) {
        url.searchParams.set('width', String(ancho));
        return url.href;
      }

      const miniatura = url.pathname.match(/\/(\d+)px-([^/]+)$/);
      if (miniatura) {
        url.pathname = url.pathname.replace(/\/\d+px-/, '/' + ancho + 'px-');
        url.search = '';
        return url.href;
      }

      if (url.hostname === 'upload.wikimedia.org' &&
          url.pathname.includes('/wikipedia/commons/') &&
          !url.pathname.includes('/thumb/')) {
        const partes = url.pathname.split('/wikipedia/commons/')[1].split('/');
        const archivo = partes.pop();
        const hash = partes.join('/');
        url.pathname = '/wikipedia/commons/thumb/' + hash + '/' + archivo + '/' +
          ancho + 'px-' + archivo;
        url.search = '';
        return url.href;
      }
    } catch (error) {
      console.warn('CIBA: no se pudo ajustar el tamaño de una imagen.', error);
    }
    return original;
  }

  function configurarImagen(img, foto, ancho, srcset) {
    const variantes = foto.variantes && typeof foto.variantes === 'object'
      ? foto.variantes
      : null;
    const resolverTamano = (tamano) => {
      const rutaLocal = variantes && variantes[String(tamano)];
      return rutaLocal ? new URL(rutaLocal, raiz).href : urlImagenOptimizada(foto.url, tamano);
    };
    img.src = resolverTamano(ancho);
    if (srcset) {
      img.srcset = srcset.map((tamano) =>
        resolverTamano(tamano) + ' ' + tamano + 'w'
      ).join(', ');
      img.sizes = '(max-width: 600px) 50vw, 220px';
    }
    img.alt = foto.alt || 'Fotografía de alimento';
    img.loading = 'lazy';
    img.decoding = 'async';
    img.fetchPriority = 'low';
    img.width = ancho;
    img.height = Math.round(ancho * 0.72);
  }

  const crear = (tag, clase, texto) => {
    const nodo = document.createElement(tag);
    if (clase) nodo.className = clase;
    if (texto !== undefined) nodo.textContent = texto;
    return nodo;
  };

  const enlazar = (nodo, url, texto) => {
    const a = crear('a', '', texto);
    a.href = url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    nodo.appendChild(a);
  };

  async function iniciar() {
    const raizUI = document.getElementById('ciba-alimentos');
    if (!raizUI) return;

    const buscador = raizUI.querySelector('#ciba-alimentos-buscar');
    const categorias = raizUI.querySelector('#ciba-alimentos-categorias');
    const lista = raizUI.querySelector('#ciba-alimentos-lista');
    const detalle = raizUI.querySelector('#ciba-alimentos-detalle');
    const estado = raizUI.querySelector('#ciba-alimentos-estado');

    try {
      const respuesta = await fetch(rutaIndice.href, { cache: 'no-cache' });
      if (!respuesta.ok) throw new Error('No se pudo cargar el índice de la biblioteca.');
      const indice = await respuesta.json();
      if (!Array.isArray(indice.archivos)) throw new Error('Índice de alimentos inválido.');
      const grupoSolicitado = raizUI.dataset.grupo;
      let alimentos = [];

      if (grupoSolicitado) {
        const categoria = (indice.categorias || []).find((item) => item.slug === grupoSolicitado);
        if (!categoria || !categoria.archivo) throw new Error('Grupo de alimentos desconocido.');
        const r = await fetch(new URL(categoria.archivo, raiz).href, { cache: 'force-cache' });
        if (!r.ok) throw new Error('No se pudo cargar el grupo: ' + grupoSolicitado);
        const datosGrupo = await r.json();
        alimentos = Array.isArray(datosGrupo.alimentos) ? datosGrupo.alimentos : [];
      } else {
        throw new Error('La página de alimentos debe indicar el grupo que va a cargar.');
      }
      let categoriaActiva = 'Todos';

      function abrirDetalle(alimento, actualizarHash = true, claveSeccion = '') {
        detalle.replaceChildren();

        const cabecera = crear('div', 'ciba-alimento-detalle-cabecera');
        const etiqueta = crear('p', 'ciba-alimento-etiqueta', alimento.categoria + ' · FICHA CIBA');
        const titulo = crear('h3', '', alimento.nombre);
        const resumen = crear('p', 'ciba-alimento-resumen', alimento.resumen);
        cabecera.append(etiqueta, titulo, resumen);

        const galeria = crear('div', 'ciba-alimento-galeria');
        const fotografias = [
          alimento.imagen_principal,
          ...(alimento.imagenes || [])
        ].filter((foto) => foto && foto.url);

        fotografias.forEach((foto) => {
          const marco = crear('figure', 'ciba-alimento-foto');
          const img = document.createElement('img');
          configurarImagen(img, foto, 960, [640, 960]);
          img.sizes = '(max-width: 720px) 100vw, 720px';
          marco.appendChild(img);

          if (foto.autor) {
            const creditos = crear('figcaption', '', '');
            creditos.append('Fotografía: ' + foto.autor + ' · ');
            enlazar(creditos, foto.atribucion_url, foto.licencia || 'Licencia');
            marco.appendChild(creditos);
          }
          galeria.appendChild(marco);
        });
        if (fotografias.length) detalle.appendChild(galeria);

        detalle.appendChild(cabecera);

        const seccion = (nombre, contenido, clave) => {
          const bloque = crear('section', 'ciba-alimento-bloque');
          bloque.id = 'alimento-' + alimento.id + '--' + clave;
          bloque.tabIndex = -1;
          bloque.style.scrollMarginTop = '110px';
          bloque.appendChild(crear('h4', '', nombre));
          if (Array.isArray(contenido)) {
            const ul = crear('ul');
            contenido.forEach((item) => {
              const li = crear('li');
              if (typeof item === 'string') li.textContent = item;
              else {
                li.appendChild(crear('strong', '', item.etapa || item.nombre || ''));
                li.appendChild(crear('p', '', item.forma || item.preparacion || ''));
                if (item.ingredientes) li.appendChild(crear('p', 'ciba-alimento-ingredientes', 'Ingredientes: ' + item.ingredientes));
              }
              ul.appendChild(li);
            });
            bloque.appendChild(ul);
          } else {
            bloque.appendChild(crear('p', '', contenido || ''));
          }
          detalle.appendChild(bloque);
        };

        seccion('¿Qué es y qué aporta?', alimento.descripcion, 'descripcion');
        seccion('Propiedades', alimento.propiedades, 'propiedades');
        seccion('¿Qué beneficios aporta?', alimento.beneficios, 'beneficios');
        seccion('¿Desde qué edad puede ofrecerse?', alimento.edad, 'edad');
        seccion('Preparación según la etapa', alimento.preparacion_por_edades, 'preparacion');
        seccion('Preparación segura', alimento.preparacion_segura, 'seguridad');
        seccion('Recetas sencillas', alimento.recetas, 'recetas');
        seccion('Precauciones', alimento.precauciones, 'precauciones');
        seccion('Conservación', alimento.conservacion, 'conservacion');

        if (alimento.video_youtube?.url) {
          const video = crear('section', 'ciba-alimento-video');
          video.id = 'alimento-' + alimento.id + '--video';
          video.tabIndex = -1;
          video.style.scrollMarginTop = '110px';
          video.appendChild(crear('h4', '', 'Video relacionado de Solo Sin Receta'));
          enlazar(video, alimento.video_youtube.url, alimento.video_youtube.titulo || 'Ver video en YouTube');
          detalle.appendChild(video);
        } else {
          const pendiente = crear('section', 'ciba-alimento-video ciba-alimento-video-pendiente', 'Video de Solo Sin Receta: pendiente de identificar un Short que trate específicamente este alimento o su preparación.');
          pendiente.id = 'alimento-' + alimento.id + '--video';
          pendiente.tabIndex = -1;
          pendiente.style.scrollMarginTop = '110px';
          detalle.appendChild(pendiente);
        }

        if (Array.isArray(alimento.fuentes) && alimento.fuentes.length) {
          const fuentes = crear('section', 'ciba-alimento-fuentes');
          fuentes.id = 'alimento-' + alimento.id + '--fuentes';
          fuentes.tabIndex = -1;
          fuentes.style.scrollMarginTop = '110px';
          fuentes.appendChild(crear('h4', '', 'Fuentes y referencias'));
          const ul = crear('ul');
          alimento.fuentes.forEach((fuente) => {
            const li = crear('li');
            li.appendChild(crear('strong', '', fuente.institucion + '. '));
            enlazar(li, fuente.url, fuente.titulo + ' °');
            li.appendChild(document.createTextNode(' ' + fuente.utilidad));
            ul.appendChild(li);
          });
          fuentes.appendChild(ul);
          detalle.appendChild(fuentes);
        }

        const volver = crear('button', 'ciba-alimentos-volver', '← Volver a todos los alimentos');
        volver.type = 'button';
        volver.addEventListener('click', () => {
          detalle.hidden = true;
          lista.hidden = false;
          if (actualizarHash) history.replaceState(null, '', location.pathname + location.search + '#biblioteca-alimentos');
          raizUI.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        detalle.appendChild(volver);

        lista.hidden = true;
        detalle.hidden = false;
        if (actualizarHash) {
          const ancla = claveSeccion ? '--' + claveSeccion : '';
          history.replaceState(null, '', location.pathname + location.search + '#alimento-' + alimento.id + ancla);
        }
        detalle.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (claveSeccion) {
          setTimeout(() => {
            const objetivo = document.getElementById('alimento-' + alimento.id + '--' + claveSeccion);
            if (objetivo) objetivo.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 100);
        }
      }

      function renderizar() {
        const consulta = normalizar(buscador.value);
        const terminos = consulta.split(/\s+/).filter((t) => t.length > 1 && !['mi','el','la','los','las','un','una','puede','pueden','dar','comer','para','desde','cuando','como','que','es','de','del','y','a'].includes(t));
        const visibles = alimentos.map((alimento) => {
          const coincideCategoria = categoriaActiva === 'Todos' || alimento.categoria === categoriaActiva;
          const texto = normalizar([
            alimento.nombre,
            ...(alimento.nombres_alternativos || []),
            alimento.resumen,
            ...(alimento.palabras_clave || [])
          ].join(' '));
          const aciertos = terminos.filter((termino) => texto.includes(termino)).length;
          return { alimento, coincideCategoria, puntuacion: terminos.length ? aciertos / terminos.length : 1 };
        }).filter((item) => item.coincideCategoria && (!consulta || item.puntuacion >= 0.5))
          .sort((a, b) => b.puntuacion - a.puntuacion)
          .map((item) => item.alimento);

        lista.replaceChildren();
        visibles.forEach((alimento) => {
          const tarjeta = crear('button', 'ciba-alimento-tarjeta');
          tarjeta.type = 'button';
          tarjeta.setAttribute('aria-label', 'Abrir ficha de ' + alimento.nombre);

          if (alimento.imagen_principal?.url) {
            const img = document.createElement('img');
            configurarImagen(img, alimento.imagen_principal, 640, [320, 640]);
            img.sizes = '(max-width: 600px) 50vw, 220px';
            tarjeta.appendChild(img);
          }
          const texto = crear('span', 'ciba-alimento-tarjeta-texto');
          texto.appendChild(crear('small', '', alimento.categoria));
          texto.appendChild(crear('strong', '', alimento.nombre));
          texto.appendChild(crear('span', '', alimento.resumen));
          tarjeta.appendChild(texto);
          tarjeta.addEventListener('click', () => abrirDetalle(alimento, true, resolverSeccion(buscador.value)?.clave || ''));
          lista.appendChild(tarjeta);
        });

        estado.textContent = visibles.length
          ? visibles.length + (visibles.length === 1 ? ' alimento disponible' : ' alimentos disponibles')
          : 'No encontramos alimentos con esa búsqueda. Prueba otra palabra.';
      }

      const nombresCategorias = ['Todos', ...new Set(alimentos.map((a) => a.categoria).filter(Boolean))];
      nombresCategorias.forEach((nombre) => {
        const boton = crear('button', nombre === 'Todos' ? 'ciba-alimentos-filtro activo' : 'ciba-alimentos-filtro', nombre);
        boton.type = 'button';
        boton.addEventListener('click', () => {
          categoriaActiva = nombre;
          categorias.querySelectorAll('button').forEach((b) => b.classList.toggle('activo', b.textContent === nombre));
          renderizar();
        });
        categorias.appendChild(boton);
      });

      buscador.addEventListener('input', renderizar);
      renderizar();

      const hash = decodeURIComponent(location.hash.replace(/^#/, ''));
      if (hash.startsWith('alimento-')) {
        const destino = hash.slice(9);
        const separador = destino.indexOf('--');
        const idAlimento = separador >= 0 ? destino.slice(0, separador) : destino;
        const claveSeccion = separador >= 0 ? destino.slice(separador + 2) : '';
        const alimento = alimentos.find((a) => a.id === idAlimento);
        if (alimento) {
          abrirDetalle(alimento, false);
          if (claveSeccion) {
            setTimeout(() => {
              const objetivo = document.getElementById('alimento-' + idAlimento + '--' + claveSeccion);
              if (objetivo) objetivo.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 80);
          }
        }
      }
    } catch (error) {
      console.error('CIBA: biblioteca de alimentos no disponible.', error);
      estado.textContent = 'La biblioteca está temporalmente indisponible. Inténtalo de nuevo más tarde.';
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar, { once: true });
  } else {
    iniciar();
  }
})();
