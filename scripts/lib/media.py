"""Validación de rutas multimedia y copia segura al artefacto público."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .errors import ValidationError
from .safety import es_ruta_segura, iterar_arbol_seguro


# Presupuesto máximo institucional para cualquier imagen publicada.
MAX_IMAGEN_BYTES = 500 * 1024
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}


@dataclass(frozen=True)
class MediaFoto:
    ruta_relativa: str
    alt: str


def validar_foto(
    ruta_valor: str,
    base_pagina: Path,
    rel_pagina: str,
    indice: int,
) -> tuple[MediaFoto | None, list[ValidationError]]:
    """Valida una ruta de foto declarada en meta.media.fotos[i].ruta."""
    errores: list[ValidationError] = []
    campo = f"media.fotos[{indice}].ruta"

    if not isinstance(ruta_valor, str) or not ruta_valor.strip():
        errores.append(ValidationError(rel_pagina, campo, "string no vacío"))
        return None, errores

    if ruta_valor.startswith(("/", "\\")) or "://" in ruta_valor:
        errores.append(ValidationError(rel_pagina, campo, "debe ser ruta relativa interna"))
        return None, errores

    partes = ruta_valor.replace("\\", "/").split("/")
    if any(p in ("..", ".") or p == "" for p in partes):
        errores.append(ValidationError(rel_pagina, campo, "no puede contener '..', '.' ni vacíos"))
        return None, errores

    candidata = base_pagina / ruta_valor
    ok, motivo = es_ruta_segura(base_pagina, candidata)
    if not ok:
        errores.append(ValidationError(rel_pagina, campo, motivo))
        return None, errores
    if not candidata.is_file():
        errores.append(ValidationError(rel_pagina, campo, "archivo no existe"))
        return None, errores

    if candidata.suffix.lower() in EXTENSIONES_IMAGEN:
        peso = candidata.stat().st_size
        if peso > MAX_IMAGEN_BYTES:
            errores.append(ValidationError(
                rel_pagina,
                campo,
                f"imagen de {peso / 1024:.1f} KB: supera el límite CIBA de 500 KB",
            ))
            return None, errores

    return MediaFoto(ruta_relativa=ruta_valor, alt=""), errores


def copiar_media_autorizada(
    origen_pagina: Path,
    destino_pagina: Path,
    fotos: list[MediaFoto],
    rel_pagina: str,
) -> list[ValidationError]:
    """Copia solo las fotos autorizadas. No copia nada más. No sigue symlinks."""
    errores: list[ValidationError] = []
    for foto in fotos:
        origen = origen_pagina / foto.ruta_relativa
        ok, motivo = es_ruta_segura(origen_pagina, origen)
        if not ok:
            errores.append(ValidationError(rel_pagina, "media.fotos", f"ruta insegura: {motivo}"))
            continue
        if not origen.is_file():
            errores.append(ValidationError(rel_pagina, "media.fotos", f"origen no es archivo: {foto.ruta_relativa}"))
            continue
        destino = destino_pagina / foto.ruta_relativa
        destino.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(origen, destino)
        except OSError as exc:
            errores.append(ValidationError(rel_pagina, "media.fotos", f"copia fallida: {exc}"))
    return errores


def verificar_destino_sin_extranos(destino_pagina: Path, permitidos: set[str], rel_pagina: str) -> list[ValidationError]:
    """Verificación defensiva: ningún archivo no autorizado en destino_pagina.

    No sigue symlinks; reporta y elimina solo archivos regulares no autorizados.
    Un symlink en destino_pagina se reporta como error (no se toca).
    """
    errores: list[ValidationError] = []
    if not destino_pagina.exists():
        return errores
    archivos, errs_walk = iterar_arbol_seguro(destino_pagina)
    errores.extend(errs_walk)
    for f in archivos:
        rel = str(f.relative_to(destino_pagina)).replace("\\", "/")
        if rel in permitidos:
            continue
        try:
            f.unlink()
        except OSError as exc:
            errores.append(ValidationError(rel_pagina, "limpieza", f"no se pudo eliminar {rel}: {exc}"))
    return errores
