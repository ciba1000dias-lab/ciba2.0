"""Rutas y constantes compartidas por los scripts de CIBA."""

from __future__ import annotations

from pathlib import Path

COLUMNAS_VALIDAS = ("C", "I", "B", "A")
COLUMNAS_CARPETAS_OFICIALES = ("c", "i", "b", "a")
RE_COLUMNA = r"^[CIBA]$"
RE_AREA = r"^[CIBA][1-9][0-9]*$"
RE_PAGINA = r"^[CIBA][1-9][0-9]*-[0-9]{2}(?:-[0-9]{2})*$"
ESTADOS_VALIDOS = ("borrador", "revision", "publicado", "archivado")


def raiz_repo() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def ruta_content(raiz: Path | None = None) -> Path:
    return (raiz or raiz_repo()) / "content"


def ruta_esquema(raiz: Path | None = None) -> Path:
    return ruta_content(raiz) / "_esquema"


def columnas_desde_disco(content_dir: Path) -> list[Path]:
    """Carpetas de columna existentes, en orden oficial c, i, b, a.

    No sigue symlinks. Devuelve solo carpetas cuyo nombre (en minúscula)
    coincide con una columna oficial. La validación estricta de nombres
    se hace en validate_content.py.
    """
    if not content_dir.is_dir():
        return []
    resultado: list[Path] = []
    for letra in COLUMNAS_CARPETAS_OFICIALES:
        candidata = content_dir / letra
        if candidata.exists() and not candidata.is_symlink() and candidata.is_dir():
            resultado.append(candidata)
    return resultado


def es_ruta_segura(base: Path, candidata: Path) -> bool:
    """Compatibilidad: delega en safety.es_ruta_segura."""
    from .safety import es_ruta_segura as _es
    ok, _ = _es(base, candidata)
    return ok
