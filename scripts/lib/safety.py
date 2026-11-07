"""Validación segura de rutas del contenido CIBA.

No sigue enlaces simbólicos y no permite salir de la raíz autorizada.
Las rutas relativas siempre se interpretan desde esa raíz.
"""
from __future__ import annotations

import os
from pathlib import Path
from .errors import ValidationError


def _absoluta_lexica(ruta: Path) -> Path:
    """Absolutiza sin resolver symlinks, para poder detectarlos antes."""
    return Path(os.path.abspath(os.fspath(ruta)))


def _cadena_hasta_raiz(ruta: Path) -> list[Path]:
    """Devuelve los ancestros desde la raíz del sistema hasta ruta."""
    partes = [ruta]
    actual = ruta
    while actual.parent != actual:
        actual = actual.parent
        partes.append(actual)
    partes.reverse()
    return partes


def _comprobar_symlinks(ruta: Path) -> tuple[bool, str]:
    for segmento in _cadena_hasta_raiz(ruta):
        try:
            if segmento.is_symlink():
                return False, f"symlink detectado: {segmento}"
        except OSError as exc:
            return False, f"no se pudo comprobar {segmento}: {exc}"
    return True, ""


def es_ruta_segura(raiz: Path, candidata: Path) -> tuple[bool, str]:
    """Valida una ruta bajo raiz; acepta candidata relativa o absoluta.

    Relativas: se interpretan respecto a raiz. Absolutas: deben estar dentro.
    Se inspeccionan los ancestros sin resolve previo, para no ocultar symlinks.
    """
    raiz_abs = _absoluta_lexica(Path(raiz))
    cand = Path(candidata)
    if cand.is_absolute():
        cand_abs = _absoluta_lexica(cand)
    else:
        if ".." in cand.parts:
            return False, "la ruta relativa contiene '..'"
        cand_abs = _absoluta_lexica(raiz_abs / cand)

    try:
        relativa = cand_abs.relative_to(raiz_abs)
    except ValueError:
        return False, f"ruta fuera de la raíz autorizada: {cand_abs}"

    ok, motivo = _comprobar_symlinks(raiz_abs)
    if not ok:
        return False, f"raíz insegura: {motivo}"

    actual = raiz_abs
    for parte in relativa.parts:
        actual = actual / parte
        ok, motivo = _comprobar_symlinks(actual)
        if not ok:
            return False, motivo

    try:
        raiz_real = raiz_abs.resolve(strict=True)
        candidata_real = cand_abs.resolve(strict=False)
        candidata_real.relative_to(raiz_real)
    except ValueError:
        return False, f"resolución fuera de la raíz autorizada: {cand_abs}"
    except (OSError, RuntimeError) as exc:
        return False, f"no se pudo resolver la ruta: {exc}"
    return True, ""


def validar_raiz(raiz: Path, ruta_relativa: str) -> list[ValidationError]:
    errores: list[ValidationError] = []
    raiz_abs = _absoluta_lexica(raiz)
    ok, motivo = _comprobar_symlinks(raiz_abs)
    if not ok:
        errores.append(ValidationError(ruta_relativa, "raíz", motivo))
        return errores
    if not raiz_abs.exists():
        errores.append(ValidationError(ruta_relativa, "raíz", "no existe"))
    elif not raiz_abs.is_dir():
        errores.append(ValidationError(ruta_relativa, "raíz", "no es directorio"))
    return errores


def listar_directorios_seguros(padre: Path, ruta_relativa: str) -> tuple[list[Path], list[ValidationError]]:
    errores: list[ValidationError] = []
    seguros: list[Path] = []
    ok, motivo = _comprobar_symlinks(_absoluta_lexica(padre))
    if not ok:
        errores.append(ValidationError(ruta_relativa, "directorio", motivo))
        return seguros, errores
    try:
        entradas = sorted(padre.iterdir(), key=lambda p: p.name)
    except OSError as exc:
        errores.append(ValidationError(ruta_relativa, "directorio", f"no legible: {exc}"))
        return seguros, errores
    for entrada in entradas:
        ok, motivo = _comprobar_symlinks(_absoluta_lexica(entrada))
        if not ok:
            errores.append(ValidationError(str(entrada), "symlink", motivo))
            continue
        try:
            if entrada.is_dir():
                seguros.append(entrada)
        except OSError as exc:
            errores.append(ValidationError(str(entrada), "directorio", f"no accesible: {exc}"))
    return seguros, errores


def iterar_arbol_seguro(raiz: Path) -> tuple[list[Path], list[ValidationError]]:
    """Recorre sin seguir symlinks y reporta también errores de os.walk."""
    errores: list[ValidationError] = []
    archivos: list[Path] = []
    raiz_original = Path(raiz)
    raiz_abs = _absoluta_lexica(raiz_original)
    errores.extend(validar_raiz(raiz_abs, str(raiz)))
    if errores:
        return archivos, errores

    def _onerror(exc: OSError) -> None:
        errores.append(ValidationError(str(getattr(exc, "filename", raiz_abs)), "recorrido", f"no se pudo leer: {exc}"))

    for actual, dirs, nombres in os.walk(raiz_abs, topdown=True, followlinks=False, onerror=_onerror):
        actual_p = Path(actual)
        dirs_seguros = []
        for nombre in dirs:
            candidata = actual_p / nombre
            ok, motivo = es_ruta_segura(raiz_abs, candidata)
            if ok and candidata.is_dir():
                dirs_seguros.append(nombre)
            else:
                errores.append(ValidationError(str(candidata), "directorio", motivo or "no es directorio seguro"))
        dirs[:] = dirs_seguros
        for nombre in nombres:
            candidata = actual_p / nombre
            ok, motivo = es_ruta_segura(raiz_abs, candidata)
            if ok:
                if raiz_original.is_absolute():
                    archivos.append(candidata)
                else:
                    archivos.append(raiz_original / candidata.relative_to(raiz_abs))
            else:
                errores.append(ValidationError(str(candidata), "archivo", motivo))
    return archivos, errores
