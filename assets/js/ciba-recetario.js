const API = 'https://damp-pine-fb21.ciba-1000dias-125.workers.dev/interpret';
const INDICE_URL = new URL('../data/alimentos-busqueda.json', import.meta.url);
const formulario = document.querySelector('#ciba-recetario-form');
const campoFecha = document.querySelector('#ciba-fecha-nacimiento');
const campoEdad = document.querySelector('#ciba-edad-valor');
const unidadEdad = document.querySelector('#ciba-edad-unidad');
const estadoEdad = document.querySelector('#ciba-edad-calculada');
const campoIngredientes = document.querySelector('#ciba-ingredientes');
const contador = document.querySelector('#ciba-contador');
const boton = document.querySelector('#ciba-receta-enviar');
const resultados = document.querySelector('#ciba-receta-resultados');
const mensaje = document.querySelector('#ciba-receta-mensaje');
const listaReconocidos = document.querySelector('#ciba-receta-reconocidos');
const desconocidos = document.querySelector('#ciba-receta-desconocidos');

let alimentos = [];

function normalizar(texto) {
  return String(texto || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

function edadEnMeses() {
  if (campoFecha.value) {
    const partes = campoFecha.value.split('-').map(Number);
    if (partes.length !== 3 || partes.some(n => !Number.isInteger(n))) return null;
    const [anio, mes, dia] = partes;
    const nacimiento = new Date(anio, mes - 1, dia);
    const hoy = new Date();
    nacimiento.setHours(0, 0, 0, 0);
    hoy.setHours(0, 0, 0, 0);
    if (nacimiento.getFullYear() !== anio || nacimiento.getMonth() !== mes - 1 ||
        nacimiento.getDate() !== dia || nacimiento > hoy) return null;
    let meses = (hoy.getFullYear() - anio) * 12 + (hoy.getMonth() - (mes - 1));
    if (hoy.getDate() < dia) meses--;
    return Math.max(0, meses);
  }
  if (campoEdad.value === '') return null;
  const valor = Number(campoEdad.value);
  const maximo = unidadEdad.value === 'anos' ? 4 : 59;
  if (!Number.isInteger(valor) || valor < 0 || valor > maximo) return null;
  return unidadEdad.value === 'anos' ? valor * 12 : valor;
}

function actualizarEdad() {
  const meses = edadEnMeses();
  if (meses === null) {
    estadoEdad.textContent = 'Indica una fecha válida o una edad entera entre 0 y 59 meses (o hasta 4 años).';
    estadoEdad.dataset.meses = '';
    return;
  }
  estadoEdad.dataset.meses = String(meses);
  const texto = meses === 1 ? '1 mes' : meses < 12 ? meses + ' meses' :
    Math.floor(meses / 12) + (Math.floor(meses / 12) === 1 ? ' año' : ' años') +
    (meses % 12 ? ' y ' + (meses % 12) + (meses % 12 === 1 ? ' mes' : ' meses') : '');
  let aviso = '';
  if (meses < 6) aviso = ' La alimentación complementaria no debe iniciarse antes de los 6 meses salvo indicación clínica individual.';
  else if (meses > 59) aviso = ' Esta primera versión del recetario cubre hasta los 59 meses.';
  estadoEdad.textContent = 'Edad calculada: ' + texto + '.' + aviso;
}

function distancia(a, b) {
  if (Math.abs(a.length - b.length) > 2) return 3;
  const fila = Array.from({length:b.length + 1}, (_,i) => i);
  for (let i = 1; i <= a.length; i++) {
    let diagonal = fila[0];
    fila[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const anterior = fila[j];
      fila[j] = Math.min(fila[j] + 1, fila[j - 1] + 1, diagonal + (a[i - 1] === b[j - 1] ? 0 : 1));
      diagonal = anterior;
    }
  }
  return fila[b.length];
}

function puntuar(alimento, terminos) {
  const textos = [alimento.nombre, ...(alimento.nombres_alternativos || []), ...(alimento.palabras_clave || [])]
    .map(normalizar).filter(Boolean);
  let mejor = 0;
  for (const termino of terminos) {
    for (const texto of textos) {
      if (texto === termino) mejor = Math.max(mejor, 5);
      else if (texto.includes(termino) || termino.includes(texto)) mejor = Math.max(mejor, 3);
      else {
        const partes = texto.split(/[^a-z0-9]+/).filter(p => p.length >= 4);
        for (const parte of partes) {
          const d = distancia(termino, parte);
          if (d <= 1 && Math.min(termino.length, parte.length) >= 5) mejor = Math.max(mejor, 2);
          else if (d <= 2 && Math.min(termino.length, parte.length) >= 7) mejor = Math.max(mejor, 1);
        }
      }
    }
  }
  return mejor;
}

function candidatosPara(texto) {
  const terminos = normalizar(texto).split(/[^a-z0-9]+/)
    .filter(t => t.length >= 3 && !['con','del','las','los','una','uno','tengo','hay','para','que','pero','poquito','pedacito'].includes(t));
  return alimentos.map(a => ({a, score:puntuar(a, terminos)}))
    .filter(x => x.score > 0)
    .sort((a,b) => b.score - a.score || a.a.nombre.localeCompare(b.a.nombre, 'es'))
    .slice(0,40)
    .map(x => ({id:x.a.id, name:x.a.nombre}));
}

function mostrarError(texto) {
  resultados.hidden = false;
  mensaje.textContent = texto;
  listaReconocidos.replaceChildren();
  desconocidos.textContent = '';
}

function mostrarResultado(data) {
  resultados.hidden = false;
  listaReconocidos.replaceChildren();
  const reconocidos = data.recognizedFoods || [];
  if (reconocidos.length) {
    mensaje.textContent = 'La IA identificó estos alimentos. Comprueba que coincidan con lo que tienes:';
    for (const item of reconocidos) {
      const li = document.createElement('li');
      li.textContent = item.name;
      listaReconocidos.appendChild(li);
    }
  } else {
    mensaje.textContent = 'No pudimos confirmar ningún alimento de la biblioteca con suficiente seguridad.';
  }
  const terminos = data.unknownTerms || [];
  desconocidos.textContent = terminos.length
    ? 'Necesitamos aclarar: ' + terminos.join(', ') + (data.clarification ? '. ' + data.clarification : '')
    : (data.clarification || '');
}

async function cargarAlimentos() {
  const respuesta = await fetch(INDICE_URL, {cache:'no-cache'});
  if (!respuesta.ok) throw new Error('No se pudo cargar la biblioteca de alimentos.');
  const datos = await respuesta.json();
  if (!Array.isArray(datos.alimentos)) throw new Error('El índice de alimentos no tiene el formato esperado.');
  alimentos = datos.alimentos;
}

function sincronizarFecha() {
  if (campoFecha.value) campoEdad.value = '';
  actualizarEdad();
}

function fechaLocalISO(fecha) {
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return anio + '-' + mes + '-' + dia;
}

campoFecha.max = fechaLocalISO(new Date());
campoFecha.addEventListener('input', sincronizarFecha);
campoFecha.addEventListener('change', sincronizarFecha);
campoEdad.addEventListener('input', () => {
  if (campoEdad.value !== '') campoFecha.value = '';
  actualizarEdad();
});
unidadEdad.addEventListener('change', () => {
  campoEdad.max = unidadEdad.value === 'anos' ? '4' : '59';
  campoEdad.placeholder = unidadEdad.value === 'anos' ? 'Ej. 2' : 'Ej. 8';
  actualizarEdad();
});
campoIngredientes.addEventListener('input', () => {
  contador.textContent = String(campoIngredientes.value.length);
});

formulario.addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const texto = campoIngredientes.value.trim();
  if (texto.length < 2) {
    mostrarError('Escribe al menos un ingrediente para comenzar.');
    return;
  }
  if (!alimentos.length) {
    mostrarError('La biblioteca todavía no está disponible. Inténtalo más tarde.');
    return;
  }
  const candidatos = candidatosPara(texto);
  if (!candidatos.length) {
    mostrarError('No encontramos términos cercanos en la biblioteca CIBA. Prueba con el nombre habitual del alimento o una variante cubana.');
    return;
  }

  boton.disabled = true;
  boton.textContent = 'Reconociendo ingredientes…';
  resultados.hidden = false;
  mensaje.textContent = 'Estamos consultando el asistente de CIBA.';
  listaReconocidos.replaceChildren();
  desconocidos.textContent = '';

  try {
    const respuesta = await fetch(API, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({ingredients:text, candidates:candidatos})
    });
    const data = await respuesta.json();
    if (!respuesta.ok || !data.ok) throw new Error(data.error || 'No se pudo completar el reconocimiento.');
    mostrarResultado(data);
  } catch (error) {
    mostrarError(error.message || 'No se pudo conectar con la IA. La biblioteca de alimentos sigue disponible.');
  } finally {
    boton.disabled = false;
    boton.innerHTML = 'Reconocer mis ingredientes <span aria-hidden="true">→</span>';
  }
});

actualizarEdad();
cargarAlimentos().catch(error => mostrarError(error.message));
