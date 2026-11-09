import { evaluarRecetas } from './ciba-recetario-motor.js';

const API = 'https://damp-pine-fb21.ciba-1000dias-125.workers.dev/interpret';
const MODO_DEMO = new URLSearchParams(window.location.search).get('demo') === '1';
const avisoDemo = document.querySelector('#ciba-receta-demo-aviso');
if (avisoDemo) avisoDemo.hidden = !MODO_DEMO;
const INDICE_URL = new URL('../data/alimentos-busqueda.json', import.meta.url);
const RECETAS_URL = new URL('../data/recetario/recetas.json', import.meta.url);
const formulario = document.querySelector('#ciba-recetario-form');
const campoFecha = document.querySelector('#ciba-fecha-nacimiento');
const campoEdadCalculada = document.querySelector('#ciba-edad-calculada');
const estadoEdad = document.querySelector('#ciba-edad-aviso');
const controlAlergias = document.querySelector('#ciba-hay-alergias');
const detalleAlergias = document.querySelector('#ciba-alergias-detalle');
const campoIngredientes = document.querySelector('#ciba-ingredientes');
const campoRestricciones = document.querySelector('#ciba-restricciones-detalle');
const contador = document.querySelector('#ciba-contador');
const boton = document.querySelector('#ciba-receta-enviar');
const resultados = document.querySelector('#ciba-receta-resultados');
const mensaje = document.querySelector('#ciba-receta-mensaje');
const listaReconocidos = document.querySelector('#ciba-receta-reconocidos');
const desconocidos = document.querySelector('#ciba-receta-desconocidos');
const propuestas = document.querySelector('#ciba-receta-propuestas');

let alimentos = [];
let recetas = [];
let ultimoResultado = null;
let resultadoConfirmado = false;

function normalizar(texto) {
  return String(texto || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

function edadEnMeses() {
  if (!campoFecha.value) return null;
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

function actualizarEdad() {
  const meses = edadEnMeses();
  if (meses === null) {
    campoEdadCalculada.value = '';
    estadoEdad.hidden = true;
    return;
  }
  const texto = meses === 1 ? '1 mes' : meses < 12 ? meses + ' meses' :
    Math.floor(meses / 12) + (Math.floor(meses / 12) === 1 ? ' año' : ' años') +
    (meses % 12 ? ' y ' + (meses % 12) + (meses % 12 === 1 ? ' mes' : ' meses') : '');
  campoEdadCalculada.value = texto;
  let aviso = '';
  if (meses < 6) aviso = 'El recetario ofrece preparaciones desde los 6 meses.';
  else if (meses > 59) aviso = 'El recetario cubre hasta los 59 meses.';
  estadoEdad.textContent = aviso;
  estadoEdad.hidden = !aviso;
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
  resultadoConfirmado = false;
  ultimoResultado = null;
  resultados.hidden = false;
  mensaje.textContent = texto;
  listaReconocidos.replaceChildren();
  desconocidos.textContent = '';
  propuestas.replaceChildren();
}

function obtenerRestricciones() {
  return [...document.querySelectorAll('input[name="restriccion"]:checked')].map(c => c.value);
}

function crearLista(items) {
  const lista = document.createElement('ul');
  for (const texto of items || []) {
    const li = document.createElement('li');
    li.textContent = texto;
    lista.appendChild(li);
  }
  return lista;
}

function mostrarRecetas(data) {
  propuestas.replaceChildren();
  const edad = edadEnMeses();
  const decision = evaluarRecetas({
    recetas: recetas.recetas || [],
    ingredientesIds: (data.recognizedFoods || []).map(item => item.id).filter(Boolean),
    edadMeses: edad,
    restricciones: obtenerRestricciones(),
    detalleRestricciones: campoRestricciones.value,
    modoDemostracion: MODO_DEMO
  });

  const titulo = document.createElement('h3');
  titulo.textContent = 'Preparaciones que coinciden';
  propuestas.appendChild(titulo);

  const aviso = document.createElement('p');
  aviso.className = 'ciba-receta-estado';

  if (decision.estado === 'menor_de_6_meses') {
    aviso.textContent = 'No mostramos recetas de alimentación complementaria antes de los 6 meses. La leche materna o la fórmula infantil indicada siguen siendo la alimentación principal.';
  } else if (decision.estado === 'fuera_de_rango') {
    aviso.textContent = 'Este recetario está preparado para edades de 6 a 59 meses.';
  } else if (decision.estado === 'falta_detalle_alergia') {
    aviso.textContent = 'Para excluir el alimento correcto, escribe cuál es la alergia diagnosticada. No vamos a adivinarla.';
  } else if (decision.estado === 'falta_detalle_intolerancia') {
    aviso.textContent = 'Especifica qué alimento o componente debe evitarse por intolerancia.';
  } else if (decision.estado === 'requiere_revision_clinica') {
    aviso.textContent = 'Con una indicación clínica adicional, no ofrecemos combinaciones automáticas. Sigue el plan del equipo de salud.';
  } else if (decision.estado === 'catalogo_sin_aprobaciones') {
    aviso.textContent = 'El catálogo culinario contiene preparaciones en revisión especializada. Ninguna está habilitada todavía, así que no te mostraremos recetas improvisadas.';
  } else if (decision.estado === 'sin_coincidencias_demo') {
    aviso.textContent = 'No hay una preparación del catálogo demostrativo que reúna todos los ingredientes reconocidos y las condiciones indicadas. No añadiremos alimentos que no mencionaste.';
  } else if (decision.estado === 'sin_coincidencias') {
    aviso.textContent = 'No hay una preparación aprobada que reúna todos los ingredientes reconocidos y las condiciones indicadas. No añadiremos alimentos que no mencionaste.';
  } else if (decision.estado === 'coincidencias_demo') {
    aviso.textContent = 'MODO DEMOSTRACIÓN: estas coincidencias proceden de preparaciones reales del catálogo CIBA, pero siguen pendientes de revisión y aprobación profesional. Se muestran para demostrar el funcionamiento del asistente; no son recomendaciones de alimentación. Comprueba siempre los ingredientes y las restricciones.';
  } else {
    aviso.textContent = 'Estas preparaciones aprobadas coinciden con los ingredientes, la edad y las restricciones indicadas. Comprueba siempre las etiquetas y evita el contacto cruzado con alérgenos.';
  }
  propuestas.appendChild(aviso);

  for (const receta of decision.recetas) {
    const tarjeta = document.createElement('article');
    tarjeta.className = 'ciba-receta-tarjeta';
    if (decision.modoDemostracion) {
      const estadoDemo = document.createElement('p');
      estadoDemo.className = 'ciba-receta-etiqueta-demo';
      estadoDemo.textContent = 'BORRADOR · NO APROBADO';
      tarjeta.appendChild(estadoDemo);
    }
    const nombre = document.createElement('h4');
    nombre.textContent = receta.nombre;
    tarjeta.appendChild(nombre);
    const descripcion = document.createElement('p');
    descripcion.textContent = receta.descripcion || '';
    tarjeta.appendChild(descripcion);
    const adaptacion = document.createElement('p');
    adaptacion.textContent = 'Para esta edad: ' + receta.adaptacion_por_edad[decision.bandaEdad];
    tarjeta.appendChild(adaptacion);
    const ingredientesTitulo = document.createElement('strong');
    ingredientesTitulo.textContent = 'Ingredientes';
    tarjeta.appendChild(ingredientesTitulo);
    tarjeta.appendChild(crearLista((receta.ingredientes || []).map(i => {
      const alimento = alimentos.find(a => a.id === i.alimento_id);
      return [i.cantidad, i.unidad, alimento ? '(' + alimento.nombre + ')' : '(' + i.alimento_id + ')'].filter(Boolean).join(' ');
    })));
    const preparacionTitulo = document.createElement('strong');
    preparacionTitulo.textContent = 'Preparación';
    tarjeta.appendChild(preparacionTitulo);
    tarjeta.appendChild(crearLista(receta.preparacion || []));
    if (receta.alertas?.length) {
      const alertas = document.createElement('p');
      alertas.textContent = 'Precauciones: ' + receta.alertas.join(' ');
      tarjeta.appendChild(alertas);
    }
    propuestas.appendChild(tarjeta);
  }
}

function mostrarAclaraciones(terminos) {
  desconocidos.replaceChildren();
  for (const termino of terminos) {
    const bloque = document.createElement('section');
    bloque.className = 'ciba-receta-aclaracion';
    const titulo = document.createElement('h3');
    titulo.textContent = '¿A qué alimento te refieres con «' + termino + '»?';
    bloque.appendChild(titulo);
    const palabras = normalizar(termino).split(/[^a-z0-9]+/).filter(t => t.length >= 3);
    const opciones = alimentos
      .map(a => ({ alimento:a, puntuacion:puntuar(a, palabras) }))
      .filter(x => x.puntuacion >= 3)
      .sort((a,b) => b.puntuacion - a.puntuacion || a.alimento.nombre.localeCompare(b.alimento.nombre, 'es'))
      .slice(0, 6);
    if (!opciones.length) {
      const ayuda = document.createElement('p');
      ayuda.textContent = 'No encontramos una variedad suficientemente clara en la biblioteca. Puedes volver a escribir el ingrediente con más detalle.';
      bloque.appendChild(ayuda);
    } else {
      const ayuda = document.createElement('p');
      ayuda.textContent = 'Puede tratarse de distintas variedades. Elige la que tienes para identificarla correctamente:';
      bloque.appendChild(ayuda);
      const lista = document.createElement('div');
      lista.className = 'ciba-receta-opciones-aclaracion';
      for (const opcion of opciones) {
        const botonOpcion = document.createElement('button');
        botonOpcion.type = 'button';
        botonOpcion.className = 'ciba-receta-opcion-aclaracion';
        const nombre = document.createElement('strong');
        nombre.textContent = opcion.alimento.nombre;
        botonOpcion.appendChild(nombre);
        if (opcion.alimento.resumen) {
          const detalle = document.createElement('span');
          detalle.textContent = opcion.alimento.resumen;
          botonOpcion.appendChild(detalle);
        }
        botonOpcion.addEventListener('click', () => {
          if (!ultimoResultado) return;
          const yaExiste = (ultimoResultado.recognizedFoods || []).some(x => x.id === opcion.alimento.id);
          if (!yaExiste) ultimoResultado.recognizedFoods = [...(ultimoResultado.recognizedFoods || []), {
            id: opcion.alimento.id, name: opcion.alimento.nombre
          }];
          ultimoResultado.unknownTerms = (ultimoResultado.unknownTerms || []).filter(x => x !== termino);
          if (!ultimoResultado.unknownTerms.length) ultimoResultado.clarification = null;
          mostrarResultado(ultimoResultado);
        });
        lista.appendChild(botonOpcion);
      }
      bloque.appendChild(lista);
    }
    desconocidos.appendChild(bloque);
  }
}

function mostrarConfirmacion(data) {
  propuestas.replaceChildren();
  const ayuda = document.createElement('p');
  ayuda.className = 'ciba-receta-estado';
  ayuda.textContent = 'Antes de buscar preparaciones, confirma que los alimentos reconocidos son exactamente los que tienes.';
  propuestas.appendChild(ayuda);
  const confirmar = document.createElement('button');
  confirmar.type = 'button';
  confirmar.className = 'ciba-receta-confirmar';
  confirmar.textContent = 'Sí, son correctos. Buscar preparaciones';
  confirmar.addEventListener('click', () => {
    resultadoConfirmado = true;
    mostrarRecetas(data);
  });
  propuestas.appendChild(confirmar);
}

function actualizarRecetasConfirmadas() {
  if (resultadoConfirmado && ultimoResultado) mostrarRecetas(ultimoResultado);
}

function mostrarResultado(data) {
  ultimoResultado = data;
  resultadoConfirmado = false;
  resultados.hidden = false;
  listaReconocidos.replaceChildren();
  const reconocidos = data.recognizedFoods || [];
  if (reconocidos.length) {
    mensaje.textContent = 'Hemos identificado estos alimentos. Comprueba que coincidan con lo que tienes:';
    for (const item of reconocidos) {
      const li = document.createElement('li');
      li.textContent = item.name;
      listaReconocidos.appendChild(li);
    }
  } else {
    mensaje.textContent = 'Todavía necesitamos identificar los ingredientes que escribiste.';
  }
  const terminos = data.unknownTerms || [];
  if (terminos.length) {
    mostrarAclaraciones(terminos);
    propuestas.replaceChildren();
    return;
  }
  desconocidos.textContent = data.clarification || '';
  if (reconocidos.length) mostrarRecetas(data);
  else propuestas.replaceChildren();
}

async function cargarDatos() {
  const [respuestaAlimentos, respuestaRecetas] = await Promise.all([
    fetch(INDICE_URL, {cache:'no-cache'}),
    fetch(RECETAS_URL, {cache:'no-cache'})
  ]);
  if (!respuestaAlimentos.ok) throw new Error('No se pudo cargar la biblioteca de alimentos.');
  if (!respuestaRecetas.ok) throw new Error('No se pudo cargar el catálogo del recetario.');
  const datosAlimentos = await respuestaAlimentos.json();
  recetas = await respuestaRecetas.json();
  if (!Array.isArray(datosAlimentos.alimentos) || !Array.isArray(recetas.recetas)) {
    throw new Error('Uno de los catálogos no tiene el formato esperado.');
  }
  alimentos = datosAlimentos.alimentos;
}

function sincronizarFecha() {
  actualizarEdad();
  actualizarRecetasConfirmadas();
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
controlAlergias.addEventListener('change', () => {
  detalleAlergias.hidden = !controlAlergias.checked;
  if (!controlAlergias.checked) {
    document.querySelectorAll('input[name="restriccion"]').forEach(c => { c.checked = false; });
    campoRestricciones.value = '';
  }
  actualizarRecetasConfirmadas();
});
campoRestricciones.addEventListener('input', actualizarRecetasConfirmadas);
document.querySelectorAll('input[name="restriccion"]').forEach(c => c.addEventListener('change', actualizarRecetasConfirmadas));
campoIngredientes.addEventListener('input', () => {
  contador.textContent = String(campoIngredientes.value.length);
  ultimoResultado = null;
  resultadoConfirmado = false;
  resultados.hidden = true;
});

formulario.addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const texto = campoIngredientes.value.trim();
  if (texto.length < 2) {
    mostrarError('Escribe al menos un ingrediente para comenzar.');
    return;
  }
  if (edadEnMeses() === null) {
    mostrarError('Indica primero una edad válida para adaptar las preparaciones.');
    return;
  }
  if (!alimentos.length || !recetas.recetas) {
    mostrarError('La biblioteca todavía no está disponible. Inténtalo más tarde.');
    return;
  }
  const candidatos = candidatosPara(texto);
  if (!candidatos.length) {
    mostrarError('No encontramos términos cercanos en la biblioteca CIBA. Prueba con el nombre habitual del alimento o una variante cubana.');
    return;
  }

  ultimoResultado = null;
  resultadoConfirmado = false;
  boton.disabled = true;
  boton.textContent = 'Reconociendo ingredientes…';
  resultados.hidden = false;
  mensaje.textContent = 'Estamos consultando el asistente de CIBA.';
  listaReconocidos.replaceChildren();
  desconocidos.textContent = '';
  propuestas.replaceChildren();

  try {
    const respuesta = await fetch(API, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({ingredients:texto, candidates:candidatos})
    });
    const data = await respuesta.json();
    if (!respuesta.ok || !data.ok) throw new Error(data.error || 'No se pudo completar el reconocimiento.');
    mostrarResultado(data);
  } catch (error) {
    mostrarError(error.message || 'No se pudo conectar con la IA. La biblioteca de alimentos sigue disponible.');
  } finally {
    boton.disabled = false;
    boton.innerHTML = 'Buscar recetas <span aria-hidden="true">→</span>';
  }
});

actualizarEdad();
cargarDatos().catch(error => mostrarError(error.message));
