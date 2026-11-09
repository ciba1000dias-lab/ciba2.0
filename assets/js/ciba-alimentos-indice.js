// CIBA · ÍNDICE LIGERO DE LA BIBLIOTECA DE ALIMENTOS
(() => {
  'use strict';
  const raiz = new URL('../../../', import.meta.url);
  const destino = document.getElementById('ciba-grupos');
  if (!destino) return;
  const normalizar = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  async function iniciar() {
    try {
      const respuesta = await fetch(new URL('assets/data/alimentos.json', raiz), { cache: 'force-cache' });
      if (!respuesta.ok) throw new Error('No se pudo cargar el índice.');
      const indice = await respuesta.json();
      destino.replaceChildren();
      (indice.categorias || []).forEach((grupo) => {
        const tarjeta = document.createElement('a');
        tarjeta.className = 'grupo-card';
        tarjeta.href = grupo.slug + '/';
        const titulo = document.createElement('strong');
        titulo.textContent = grupo.nombre;
        const descripcion = document.createElement('span');
        descripcion.textContent = 'Explora las fichas, imágenes y orientaciones de este grupo.';
        const cantidad = document.createElement('small');
        cantidad.textContent = (grupo.cantidad || 0) + ' ALIMENTOS · EXPLORAR →';
        tarjeta.append(titulo, descripcion, cantidad);
        destino.appendChild(tarjeta);
      });
      if (!destino.children.length) throw new Error('No hay grupos disponibles.');
    } catch (error) {
      console.error('CIBA: no se pudo abrir el índice de alimentos.', error);
      destino.textContent = 'La biblioteca está temporalmente indisponible. Inténtalo de nuevo más tarde.';
    }
  }
  iniciar();
})();
