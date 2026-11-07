// CIBA · app.js — bootstrap mínimo. NO Index, NO buscador, NO formularios.
import { CIBA, BASE_URL, rutaPublica } from './core/config.js';
import { cargarCatalogo } from './core/catalog.js';
import * as dom from './core/dom.js';
async function iniciar() {
  window.CIBA = Object.freeze({ config: CIBA, BASE_URL, rutaPublica, cargarCatalogo, dom });
  document.documentElement.dataset.cibaListo = 'true';
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', iniciar, { once: true });
} else {
  iniciar();
}
