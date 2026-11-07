// CIBA · core/catalog.js
import { CIBA } from './config.js';
let _cache = null;
let _promesa = null;
export class CatalogError extends Error {
  constructor(mensaje, causa) {
    super(mensaje);
    this.name = 'CatalogError';
    this.causa = causa;
  }
}
export function cargarCatalogo({ forzar = false } = {}) {
  if (_cache && !forzar) return Promise.resolve(_cache);
  if (_promesa && !forzar) return _promesa;
  _promesa = fetch(CIBA.rutas.catalogo, { cache: 'no-cache' })
    .then((r) => {
      if (!r.ok) throw new CatalogError(`HTTP ${r.status} al cargar catálogo`);
      return r.json();
    })
    .then((json) => { _cache = json; _promesa = null; return json; })
    .catch((err) => {
      _promesa = null;
      throw err instanceof CatalogError ? err : new CatalogError('Error de red al cargar catálogo', err);
    });
  return _promesa;
}
export function limpiarCacheCatalogo() { _cache = null; _promesa = null; }
