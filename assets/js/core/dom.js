// CIBA · core/dom.js
export const qs = (sel, raiz = document) => raiz.querySelector(sel);
export const qsa = (sel, raiz = document) => Array.from(raiz.querySelectorAll(sel));
export function crear(etiqueta, props = {}, hijos = []) {
  const el = document.createElement(etiqueta);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') el.className = v;
    else if (k === 'dataset') Object.assign(el.dataset, v);
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (v !== undefined && v !== null) el.setAttribute(k, String(v));
  }
  const lista = Array.isArray(hijos) ? hijos : [hijos];
  for (const h of lista) {
    if (h == null) continue;
    el.append(h instanceof Node ? h : document.createTextNode(String(h)));
  }
  return el;
}
export function vaciar(el) { while (el.firstChild) el.removeChild(el.firstChild); }
