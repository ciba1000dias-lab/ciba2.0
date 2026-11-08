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
      const grupos = await Promise.all(indice.archivos.map(async (archivo) => {
        const r = await fetch(new URL(archivo, raiz).href, { cache: 'no-cache' });
        if (!r.ok) throw new Error('No se pudo cargar: ' + archivo);
        return r.json();
      }));
      const alimentos = grupos.flatMap((grupo) => Array.isArray(grupo.alimentos) ? grupo.alimentos : []);
      let categoriaActiva = 'Todos';

      function abrirDetalle(alimento, actualizarHash = true) {
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
          img.src = foto.url;
          img.alt = foto.alt || alimento.nombre;
          img.loading = 'lazy';
          img.decoding = 'async';
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

        const seccion = (nombre, contenido) => {
          const bloque = crear('section', 'ciba-alimento-bloque');
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

        seccion('¿Qué es y qué aporta?', alimento.descripcion);
        seccion('Propiedades', alimento.propiedades);
        seccion('¿Qué beneficios aporta?', alimento.beneficios);
        seccion('¿Desde qué edad puede ofrecerse?', alimento.edad);
        seccion('Preparación según la etapa', alimento.preparacion_por_edades);
        seccion('Preparación segura', alimento.preparacion_segura);
        seccion('Recetas sencillas', alimento.recetas);
        seccion('Precauciones', alimento.precauciones);
        seccion('Conservación', alimento.conservacion);

        if (alimento.video_youtube?.url) {
          const video = crear('section', 'ciba-alimento-video');
          video.appendChild(crear('h4', '', 'Video relacionado de Solo Sin Receta'));
          enlazar(video, alimento.video_youtube.url, alimento.video_youtube.titulo || 'Ver video en YouTube');
          detalle.appendChild(video);
        } else {
          const pendiente = crear('p', 'ciba-alimento-video-pendiente', 'Video de Solo Sin Receta: pendiente de identificar un Short que trate específicamente este alimento o su preparación.');
          detalle.appendChild(pendiente);
        }

        if (Array.isArray(alimento.fuentes) && alimento.fuentes.length) {
          const fuentes = crear('section', 'ciba-alimento-fuentes');
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
          raizUI.querySelector('#biblioteca-alimentos').scrollIntoView({ behavior: 'smooth' });
        });
        detalle.appendChild(volver);

        lista.hidden = true;
        detalle.hidden = false;
        if (actualizarHash) history.replaceState(null, '', location.pathname + location.search + '#alimento-' + alimento.id);
        detalle.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }

      function renderizar() {
        const consulta = normalizar(buscador.value);
        const terminos = consulta.split(/\\s+/).filter((t) => t.length > 1 && !['mi','el','la','los','las','un','una','puede','pueden','dar','comer','para','desde','cuando','como','que','es','de','del','y','a'].includes(t));
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
            img.src = alimento.imagen_principal.url;
            img.alt = alimento.imagen_principal.alt || alimento.nombre;
            img.loading = 'lazy';
            tarjeta.appendChild(img);
          }
          const texto = crear('span', 'ciba-alimento-tarjeta-texto');
          texto.appendChild(crear('small', '', alimento.categoria));
          texto.appendChild(crear('strong', '', alimento.nombre));
          texto.appendChild(crear('span', '', alimento.resumen));
          tarjeta.appendChild(texto);
          tarjeta.addEventListener('click', () => abrirDetalle(alimento));
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
        const alimento = alimentos.find((a) => a.id === hash.slice(9));
        if (alimento) abrirDetalle(alimento, false);
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
