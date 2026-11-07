// CIBA · core/config.js
function resolverBase() {
  const baseTag = document.querySelector('base[href]');
  if (baseTag) return new URL(baseTag.href, document.baseURI).href;
  return new URL('.', document.baseURI).href;
}
export const BASE_URL = resolverBase();
export const CIBA = Object.freeze({
  nombre: 'CIBA',
  columnas: Object.freeze(['C', 'I', 'B', 'A']),
  whatsapp: '+5350861330',
  rutas: Object.freeze({
    catalogo: new URL('data/catalogo.json', BASE_URL).href,
    columnas: new URL('data/columnas.json', BASE_URL).href,
    areas: new URL('data/areas.json', BASE_URL).href
  })
});
export function rutaPublica(relativa) {
  return new URL(relativa, BASE_URL).href;
}
