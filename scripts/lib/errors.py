"""Errores estructurados del pipeline de contenidos CIBA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ValidationError:
    ruta: str
    campo: str
    mensaje: str

    def __str__(self) -> str:
        return f"[{self.ruta}] {self.campo}: {self.mensaje}"


class CIBAValidationError(Exception):
    def __init__(self, errores: Iterable[ValidationError]) -> None:
        self.errores = list(errores)
        super().__init__(f"{len(self.errores)} error(es) de validación")

    def resumen(self) -> str:
        return "\n".join(str(e) for e in self.errores)
