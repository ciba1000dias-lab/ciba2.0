// Motor determinista del recetario CIBA.
// No genera recetas: solo filtra preparaciones aprobadas del catálogo oficial.
const BANDAS = [
  { min: 6, max: 8, key: '6-8' },
  { min: 9, max: 11, key: '9-11' },
  { min: 12, max: 23, key: '12-23' },
  { min: 24, max: 59, key: '24-59' }
];

const ALERGENOS_POR_ALIMENTO = {
  'leche-vaca': ['leche', 'lacteos'],
  'leche-chiva': ['leche', 'lacteos'],
  'leche-bufala': ['leche', 'lacteos'],
  'leche-camella': ['leche', 'lacteos'],
  'leche-polvo-entera': ['leche', 'lacteos'],
  'leche-polvo-descremada': ['leche', 'lacteos'],
  'leche-evaporada': ['leche', 'lacteos'],
  'leche-condensada': ['leche', 'lacteos'],
  'yogur-natural': ['leche', 'lacteos'],
  'yogur-chiva': ['leche', 'lacteos'],
  'yogur-probiotico': ['leche', 'lacteos'],
  'yogur-vasito-pascual': ['leche', 'lacteos'],
  'kefir-natural': ['leche', 'lacteos'],
  'queso-fresco-pasteurizado': ['leche', 'lacteos'],
  'queso-blanco': ['leche', 'lacteos'],
  'requeson': ['leche', 'lacteos'],
  'huevo-gallina': ['huevo'],
  'huevo-codorniz': ['huevo'],
  'pescado-blanco': ['pescado'],
  'atun': ['pescado'],
  'salmon': ['pescado'],
  'sardina': ['pescado'],
  'camaron': ['crustaceos'],
  'langosta': ['crustaceos'],
  'cangrejo': ['crustaceos'],
  'soya': ['soya'],
  'frijol-negro': ['legumbres'],
  'frijol-colorado': ['legumbres'],
  'garbanzos': ['legumbres'],
  'lentejas': ['legumbres'],
  'chicharos': ['legumbres'],
  'mani': ['mani', 'frutos-secos'],
  'almendra': ['frutos-secos'],
  'nuez': ['frutos-secos'],
  'ajonjoli': ['sesamo'],
  'trigo': ['trigo-gluten'],
  'pan': ['trigo-gluten'],
  'pasta-trigo': ['trigo-gluten']
};

const ALIAS_ALERGENOS = [
  { key: 'leche', terms: ['leche', 'proteina de leche', 'proteina de leche de vaca', 'caseina', 'suero de leche', 'lacteos', 'lacteo'] },
  { key: 'lacteos', terms: ['lactosa', 'intolerancia a la lactosa'] },
  { key: 'huevo', terms: ['huevo', 'huevos', 'clara', 'yema'] },
  { key: 'pescado', terms: ['pescado', 'atun', 'salmon', 'sardina', 'merluza'] },
  { key: 'crustaceos', terms: ['camaron', 'camarones', 'langosta', 'cangrejo', 'crustaceos'] },
  { key: 'soya', terms: ['soya', 'soja'] },
  { key: 'mani', terms: ['mani', 'cacahuete', 'cacahuate'] },
  { key: 'frutos-secos', terms: ['almendra', 'nuez', 'avellana', 'anacardo', 'pistacho', 'frutos secos'] },
  { key: 'sesamo', terms: ['sesamo', 'ajonjoli'] },
  { key: 'trigo-gluten', terms: ['trigo', 'gluten', 'cebada', 'centeno'] },
  { key: 'legumbres', terms: ['legumbres', 'frijol', 'frijoles', 'lentejas', 'garbanzos', 'chicharos'] }
];

function normalizar(texto) {
  return String(texto || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

export function identificarAlergenos(detalle) {
  const texto = normalizar(detalle);
  const encontrados = [];
  for (const grupo of ALIAS_ALERGENOS) {
    if (grupo.terms.some(term => texto.includes(normalizar(term)))) encontrados.push(grupo.key);
  }
  return [...new Set(encontrados)];
}

function bandaParaEdad(meses) {
  return BANDAS.find(b => meses >= b.min && meses <= b.max) || null;
}

function alergenosDeReceta(receta) {
  const encontrados = new Set((receta.alergenos || []).map(normalizar));
  for (const ingrediente of receta.ingredientes || []) {
    for (const alergeno of ALERGENOS_POR_ALIMENTO[ingrediente.alimento_id] || []) encontrados.add(alergeno);
  }
  return encontrados;
}

function recetaVegetariana(receta) {
  const ids = (receta.ingredientes || []).map(i => i.alimento_id);
  const categoriasAnimales = /pollo|pavo|res|cerdo|carne|pescado|atun|salmon|sardina|camaron|langosta|cangrejo|pulpo|calamar|ostion|cobo|higado/;
  return !ids.some(id => categoriasAnimales.test(id));
}

export function evaluarRecetas({ recetas, ingredientesIds, edadMeses, restricciones = [], detalleRestricciones = '' }) {
  if (!Number.isInteger(edadMeses)) return { estado: 'edad_invalida', recetas: [] };
  if (edadMeses < 6) return { estado: 'menor_de_6_meses', recetas: [] };
  if (edadMeses > 59) return { estado: 'fuera_de_rango', recetas: [] };

  const seleccionadas = new Set(restricciones);
  const alergiaDeclarada = seleccionadas.has('alergia');
  const intoleranciaDeclarada = seleccionadas.has('intolerancia');
  const otraDeclarada = seleccionadas.has('otra');
  const alergenos = identificarAlergenos(detalleRestricciones);

  if (otraDeclarada) return { estado: 'requiere_revision_clinica', recetas: [] };
  if (alergiaDeclarada && !alergenos.length) return { estado: 'falta_detalle_alergia', recetas: [] };
  if (intoleranciaDeclarada && !alergenos.length) return { estado: 'falta_detalle_intolerancia', recetas: [] };

  const edad = bandaParaEdad(edadMeses);
  const ids = new Set(ingredientesIds || []);
  const publicadas = (recetas || []).filter(r => r.publicable === true && r.estado === 'aprobada');
  const coincidencias = publicadas.filter(receta => {
    if (edadMeses < (receta.edad_minima_meses ?? 6) || edadMeses > (receta.edad_maxima_meses ?? 59)) return false;
    if (!receta.adaptacion_por_edad || !receta.adaptacion_por_edad[edad.key]) return false;
    const obligatorios = (receta.ingredientes || []).filter(i => i.obligatorio !== false);
    if (!obligatorios.length || !obligatorios.every(i => ids.has(i.alimento_id))) return false;
    if (seleccionadas.has('vegetariana') && !recetaVegetariana(receta)) return false;
    const presentes = alergenosDeReceta(receta);
    if (alergenos.some(a => presentes.has(a))) return false;
    return true;
  });

  return {
    estado: coincidencias.length ? 'coincidencias' : publicadas.length ? 'sin_coincidencias' : 'catalogo_sin_aprobaciones',
    bandaEdad: edad.key,
    alergenosDetectados: alergenos,
    recetas: coincidencias
  };
}
