# CIBA · Convenciones de identificadores, metadatos y flujo de contenidos

> Documento interno. No se publica en GitHub Pages.
> Versión 1.4 · consolidación de seguridad y publicación.

## 1. Identificadores

| Entidad | Regex | Ejemplo |
|---|---|---|
| Columna | `^[CIBA]$` | `C` |
| Área | `^[CIBA][1-9][0-9]*$` | `C21` |
| Página | `^[CIBA][1-9][0-9]*-[0-9]{2}$` | `C21-01` |

## 2. Estructura física

    content/c|i|b|a/<AREA>/area.json
    content/c|i|b|a/<AREA>/<PAG>/meta.json
    content/c|i|b|a/<AREA>/<PAG>/index.html
    content/c|i|b|a/<AREA>/<PAG>/media/**   (opcional, declarado)

Las carpetas de columna se llaman exactamente `c`, `i`, `b`, `a` (minúscula). Una carpeta `C` no sustituye a `c`.

## 3. `columnas.json`

- Raíz: solo `version` (entero estricto, no bool) y `columnas` (exactamente 4).
- Cada columna: `id` ∈ {C,I,B,A}, `titulo` 3–120, `descripcion` 10–300, `orden` entero ≥ 0 (no bool), `icono` 1–40.
- Sin campos desconocidos en ningún nivel.

## 4. `area.json`

- `id` = nombre de carpeta. `titulo` 3–120. `descripcion` 10–300. `columna` ∈ {C,I,B,A}. `orden` entero ≥ 0 (no bool).
- Sin campos desconocidos.

## 5. `meta.json`

- `id` = `<area>-NN`. `titulo` 3–120. `descripcion` 10–300. `columna` = letra de carpeta. `area` = `id` de `area.json`.
- `palabras_clave` 1–15, cada 2–40, minúsculas, sin espacios extremos.
- `estado` ∈ {borrador, revision, publicado, archivado}.
- `fecha_publicacion` con formato estricto `YYYY-MM-DD` (mes y día con dos dígitos), fecha válida y no futura. Los campos obligatorios no admiten `null`.
- `mostrar_en_columna`, `mostrar_en_area` booleanos.
- `media` opcional, estructura validada.
- `enlaces_externos` opcional, URL http(s).
- `whatsapp_consulta` booleano opcional.
- Sin campos desconocidos.

## 6. `meta.media`

- `videos|mapas`: `[{proveedor, id, titulo?}]`.
- `fotos`: `[{ruta, alt?}]`. `ruta` relativa, sin `/` inicial, sin `://`, sin `..`/`.`/vacíos, existente, dentro de la página, sin symlink.
- Sin campos desconocidos en ningún nivel.

## 7. Estados

- `borrador`, `revision`: nunca se publican.
- `publicado`: se publica; requiere `index.html` ≥ 200 bytes sin symlink.
- `archivado`: fuera del catálogo.

## 8. Relación esquemas ↔ validadores

`meta.schema.json` y `area.schema.json` son **contratos de referencia**. La fuente ejecutable es Python. `tests/test_schema_consistency.py` verifica que no diverjan. Si cambias un esquema, actualiza el validador correspondiente y viceversa.

## 9. Allowlist de publicación

Solo `index.html` y fotos declaradas y validadas. Verificación defensiva elimina lo no autorizado. Nunca se publican `meta.json`, `area.json`, borradores, symlinks ni archivos desconocidos.

## 10. Añadir una página

1. Elegir área. Si no existe, crear `content/<col>/<AREA>/area.json`.
2. Crear `content/<col>/<AREA>/<PAG>/`.
3. Crear `meta.json` completo.
4. Crear `index.html` ≥ 200 bytes.
5. `python scripts/validate_content.py --src content`.
6. `python scripts/build_catalog.py --src content --out dist`.

## 11. Añadir un área

1. Crear `content/<col>/<AREA>/`.
2. Crear `area.json` con `id` = nombre de carpeta.

## 12. Reglas de oro

- `dist/data/catalogo.json` es siempre output.
- `dist/` se reemplaza solo si validación y build son correctos.
- Solo se publican archivos de la allowlist.
- Nunca se siguen symlinks.
- WhatsApp único: `+5350861330`.
- Sin frameworks pesados.
