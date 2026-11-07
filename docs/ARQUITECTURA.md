# CIBA · Arquitectura técnica

> Documento interno. No se publica en GitHub Pages.
> Versión 1.4 · consolidación de seguridad y publicación.

## 1. Principios

1. Descubrimiento automático de áreas por `area.json` y páginas por `meta.json`.
2. Separación de capas: `content/` (fuente) → `scripts/` (generación) → `dist/` (público).
3. Identificadores técnicos inmutables. Los códigos no se muestran al visitante.
4. Validación antes de publicar; cualquier inconsistencia aborta el build.
5. Un único catálogo público: `dist/data/catalogo.json`.
6. Build atómico con recuperación real.
7. Allowlist de publicación.
8. **Nunca se siguen symlinks** en origen ni en directorios intermedios.
9. Rutas relativas resueltas en runtime.
10. Mobile-first, sin frameworks pesados.

## 2. Modelo de tres capas

    content/  →  scripts/  →  dist/

## 3. Descubrimiento

- Área existe si y solo si existe `content/<col>/<AREA>/area.json`.
- Página existe si y solo si existe `content/<col>/<AREA>/<PAG>/meta.json`.
- Cada área se registra exactamente una vez, incluso sin páginas.
- El descubrimiento no sigue symlinks ni en carpetas ni en archivos.

## 4. Seguridad de rutas

Módulo `scripts/lib/safety.py`:

- `es_ruta_segura(raiz, candidata)`: interpreta rutas relativas desde la raíz autorizada; acepta rutas absolutas solo dentro de ella; inspecciona raíz y ancestros antes de resolver; rechaza symlinks y escapes.
- `listar_directorios_seguros`: itera sin seguir symlinks; reporta symlinks como error.
- `iterar_arbol_seguro`: `os.walk(..., followlinks=False, onerror=...)` + filtro explícito; reporta errores de acceso y no procesa rutas inseguras.

Un error de seguridad detiene la validación con código 1 y deja `dist/` intacto.

## 5. Validaciones obligatorias

- Cuatro columnas físicas: `content/c`, `content/i`, `content/b`, `content/a`. Sin duplicados por mayúsculas ni nombres inválidos.
- `columnas.json`: raíz solo `version` (entero estricto, no bool) y `columnas` (exactamente 4, ids C/I/B/A una vez, campos y tipos estrictos, sin campos desconocidos).
- `area.json` y `meta.json`: campos obligatorios no nulos, tipos estrictos (`bool` no es `int`), longitudes, regex, estados, fecha estricta `YYYY-MM-DD` no futura, media válida con rutas seguras y existentes, URLs http(s), sin campos desconocidos.
- Correspondencia columna↔área↔metadatos y página↔área por prefijo.
- Sin IDs duplicados.
- Páginas `publicado` con `index.html` ≥ 200 bytes, sin symlink.

## 6. Catálogo público

`dist/data/catalogo.json`:

    {
      "version": 1,
      "generado": "YYYY-MM-DD",
      "columnas": [...],
      "areas": [...],   // todas, con o sin páginas, sin duplicados
      "paginas": [...]
    }

## 7. Allowlist de publicación

Solo `index.html` y las fotos declaradas en `meta.media.fotos[]` que pasen validación. Verificación defensiva posterior elimina cualquier archivo no autorizado. Nunca se publican `meta.json`, `area.json`, borradores, symlinks ni archivos desconocidos.

## 8. Build atómico con recuperación

1. Validar. Fallo → exit 1, `dist/` intacto.
2. Construir en `dist.tmp/`.
3. `dist/` → `dist.old/`, luego `dist.tmp/` → `dist/`.
4. Verificación de `dist/data/catalogo.json`.
5. Si OK: borrar `dist.old/`. Si falla cualquier paso: `dist.old/` → `dist/`.
6. Cualquier excepción → `dist.tmp/` eliminado, `dist/` intacto.

## 9. Relación esquemas ↔ validadores

`meta.schema.json` y `area.schema.json` son **contratos de referencia**, no validadores ejecutables. La fuente ejecutable es Python:

- `scripts/lib/meta_reader.py` implementa el contrato de `meta.json`.
- `scripts/lib/area_reader.py` implementa el contrato de `area.json`.
- `scripts/lib/columnas_reader.py` implementa el contrato de `columnas.json`.

La consistencia se verifica con `tests/test_schema_consistency.py`, que compara los `enum`, patrones y longitudes entre esquemas y validadores. Si un esquema cambia sin tocar el validador (o al revés), la prueba falla.

## 10. Publicación con GitHub Pages

El único workflow es `.github/workflows/static.yml`. En cada ejecución:

1. Ejecuta la suite `unittest`.
2. Valida `content/`.
3. Construye el sitio en `dist/`.
4. Publica exclusivamente `dist/` como artefacto de GitHub Pages.

No se crea un segundo workflow y nunca se publica la raíz del repositorio. El repositorio público sigue siendo visible en GitHub; esta separación solo controla qué archivos se sirven como sitio web.

## 11. Multimedia

- Logos, iconos, ilustraciones y fotos optimizadas en `assets/img/` o referenciadas desde `meta.media.fotos`.
- Vídeos y mapas externos: `meta.media.videos|mapas`.
- Documentos grandes: `enlaces_externos`.
- Interactivos: `assets/js/modules/`.

## 12. Buscador Nayara y Turey (etapa posterior)

Buscador compartido previsto para una etapa posterior; consultará `catalogo.paginas`. Sin resultados podrá orientar hacia WhatsApp `+5350861330`. No se almacenan datos personales en el catálogo público. El buscador aún no está implementado.
