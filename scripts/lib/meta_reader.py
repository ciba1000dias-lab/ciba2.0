
"""Validación estricta del meta.json de cada página CIBA."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .errors import ValidationError
from .media import MediaFoto, validar_foto
from .paths import RE_AREA, RE_PAGINA, COLUMNAS_VALIDAS, ESTADOS_VALIDOS
from .safety import es_ruta_segura

CAMPOS_OBLIGATORIOS = (
    "id", "titulo", "descripcion", "columna", "area",
    "palabras_clave", "estado", "fecha_publicacion",
    "mostrar_en_columna", "mostrar_en_area",
)
CAMPOS_OPCIONALES = (
    "media",
    "enlaces_externos",
    "whatsapp_consulta",
    "subseccion",
    "preview_publica",
)
CAMPOS_MEDIA = ("videos", "mapas", "fotos")
CAMPOS_MEDIA_VIDEO_MAPA = ("proveedor", "id", "titulo")
CAMPOS_MEDIA_FOTO = ("ruta", "alt")


@dataclass
class PaginaMeta:
    ruta_relativa: str
    ruta_fisica: Path
    datos: dict[str, Any] = field(default_factory=dict)
    fotos_validadas: list[MediaFoto] = field(default_factory=list)


def _fecha_iso(valor: str) -> date | None:
    if not isinstance(valor, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


def _url_http(valor: Any) -> bool:
    if not isinstance(valor, str):
        return False
    p = urlparse(valor)
    return p.scheme in ("http", "https") and bool(p.netloc)


def leer_meta(
    ruta_meta: Path,
    ruta_relativa: str,
    *,
    hoy: date | None = None,
) -> tuple[PaginaMeta | None, list[ValidationError]]:
    errores: list[ValidationError] = []

    if not ruta_meta.is_file():
        errores.append(ValidationError(ruta_relativa, "meta.json", "archivo ausente"))
        return None, errores

    if ruta_meta.is_symlink():
        errores.append(ValidationError(ruta_relativa, "meta.json", "es symlink"))
        return None, errores

    try:
        datos = json.loads(ruta_meta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errores.append(ValidationError(ruta_relativa, "meta.json", f"JSON inválido: {exc}"))
        return None, errores

    if not isinstance(datos, dict):
        errores.append(ValidationError(ruta_relativa, "meta.json", "debe ser objeto JSON"))
        return None, errores

    permitidos = set(CAMPOS_OBLIGATORIOS) | set(CAMPOS_OPCIONALES)
    extra = set(datos.keys()) - permitidos

    if extra:
        errores.append(
            ValidationError(ruta_relativa, "meta.json", f"campos desconocidos: {sorted(extra)}")
        )

    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in datos:
            errores.append(ValidationError(ruta_relativa, campo, "campo obligatorio ausente"))
        elif datos[campo] is None:
            errores.append(ValidationError(ruta_relativa, campo, "no puede ser null"))

    id_ = datos.get("id")
    if id_ is not None:
        if not isinstance(id_, str):
            errores.append(ValidationError(ruta_relativa, "id", "string"))
        elif not re.match(RE_PAGINA, id_):
            errores.append(ValidationError(ruta_relativa, "id", f"formato inválido: {id_!r}"))

    titulo = datos.get("titulo")
    if titulo is not None and (not isinstance(titulo, str) or not (3 <= len(titulo) <= 120)):
        errores.append(ValidationError(ruta_relativa, "titulo", "3–120"))

    desc = datos.get("descripcion")
    if desc is not None and (not isinstance(desc, str) or not (10 <= len(desc) <= 300)):
        errores.append(ValidationError(ruta_relativa, "descripcion", "10–300"))

    col = datos.get("columna")
    if col is not None and col not in COLUMNAS_VALIDAS:
        errores.append(ValidationError(ruta_relativa, "columna", f"inválido: {col!r}"))

    area = datos.get("area")
    if area is not None:
        if not isinstance(area, str):
            errores.append(ValidationError(ruta_relativa, "area", "string"))
        elif not re.match(RE_AREA, area):
            errores.append(ValidationError(ruta_relativa, "area", f"inválido: {area!r}"))

    pk = datos.get("palabras_clave")
    if pk is not None:
        if not isinstance(pk, list):
            errores.append(ValidationError(ruta_relativa, "palabras_clave", "lista"))
        else:
            if not (1 <= len(pk) <= 15):
                errores.append(ValidationError(ruta_relativa, "palabras_clave", "1–15"))

            for i, kw in enumerate(pk):
                if not isinstance(kw, str) or not (2 <= len(kw) <= 40):
                    errores.append(
                        ValidationError(ruta_relativa, f"palabras_clave[{i}]", "string 2–40")
                    )
                elif kw != kw.strip() or kw != kw.lower():
                    errores.append(
                        ValidationError(
                            ruta_relativa,
                            f"palabras_clave[{i}]",
                            "minúsculas sin espacios",
                        )
                    )

    estado = datos.get("estado")
    if estado is not None and estado not in ESTADOS_VALIDOS:
        errores.append(ValidationError(ruta_relativa, "estado", f"inválido: {estado!r}"))

    fp = datos.get("fecha_publicacion")
    if fp is not None:
        if not isinstance(fp, str):
            errores.append(ValidationError(ruta_relativa, "fecha_publicacion", "string"))
        else:
            f = _fecha_iso(fp)
            if f is None:
                errores.append(ValidationError(ruta_relativa, "fecha_publicacion", "YYYY-MM-DD"))
            elif f > (hoy or date.today()):
                errores.append(ValidationError(ruta_relativa, "fecha_publicacion", "no futura"))

    # La subsección es una clasificación temática opcional.
    subseccion = datos.get("subseccion")
    if "subseccion" in datos:
        if not isinstance(subseccion, str) or not (3 <= len(subseccion) <= 80):
            errores.append(
                ValidationError(ruta_relativa, "subseccion", "string de 3–80 caracteres")
            )
        elif subseccion != subseccion.strip():
            errores.append(
                ValidationError(ruta_relativa, "subseccion", "sin espacios al inicio o final")
            )

    for b in ("mostrar_en_columna", "mostrar_en_area", "whatsapp_consulta", "preview_publica"):
        if b in datos and not isinstance(datos[b], bool):
            errores.append(ValidationError(ruta_relativa, b, "booleano"))

    fotos_validadas: list[MediaFoto] = []
    media = datos.get("media")

    if "media" in datos and media is None:
        errores.append(ValidationError(ruta_relativa, "media", "no puede ser null"))

    if media is not None:
        if not isinstance(media, dict):
            errores.append(ValidationError(ruta_relativa, "media", "objeto"))
        else:
            extra_m = set(media.keys()) - set(CAMPOS_MEDIA)
            if extra_m:
                errores.append(
                    ValidationError(ruta_relativa, "media", f"desconocidos: {sorted(extra_m)}")
                )

            for clave in ("videos", "mapas"):
                if clave in media:
                    if not isinstance(media[clave], list):
                        errores.append(ValidationError(ruta_relativa, f"media.{clave}", "lista"))
                        continue

                    for j, item in enumerate(media[clave]):
                        pref = f"media.{clave}[{j}]"

                        if not isinstance(item, dict):
                            errores.append(ValidationError(ruta_relativa, pref, "objeto"))
                            continue

                        extra_item = set(item.keys()) - set(CAMPOS_MEDIA_VIDEO_MAPA)
                        if extra_item:
                            errores.append(
                                ValidationError(
                                    ruta_relativa,
                                    pref,
                                    f"desconocidos: {sorted(extra_item)}",
                                )
                            )

                        for c in ("proveedor", "id"):
                            if c not in item or not isinstance(item[c], str) or not item[c]:
                                errores.append(
                                    ValidationError(ruta_relativa, f"{pref}.{c}", "string no vacío")
                                )

                        if "titulo" in item and not isinstance(item["titulo"], str):
                            errores.append(
                                ValidationError(ruta_relativa, f"{pref}.titulo", "string")
                            )

            if "fotos" in media:
                if not isinstance(media["fotos"], list):
                    errores.append(ValidationError(ruta_relativa, "media.fotos", "lista"))
                else:
                    base_pagina = ruta_meta.parent

                    for j, item in enumerate(media["fotos"]):
                        pref = f"media.fotos[{j}]"

                        if not isinstance(item, dict):
                            errores.append(ValidationError(ruta_relativa, pref, "objeto"))
                            continue

                        extra_item = set(item.keys()) - set(CAMPOS_MEDIA_FOTO)
                        if extra_item:
                            errores.append(
                                ValidationError(
                                    ruta_relativa,
                                    pref,
                                    f"desconocidos: {sorted(extra_item)}",
                                )
                            )

                        ruta_val = item.get("ruta")
                        foto, errs = validar_foto(
                            ruta_val, base_pagina, ruta_relativa, j
                        )
                        errores.extend(errs)

                        if foto is not None:
                            alt = item.get("alt", "")

                            if not isinstance(alt, str):
                                errores.append(
                                    ValidationError(ruta_relativa, f"{pref}.alt", "string")
                                )
                                continue

                            fotos_validadas.append(
                                MediaFoto(ruta_relativa=foto.ruta_relativa, alt=alt)
                            )

    enlaces = datos.get("enlaces_externos")

    if "enlaces_externos" in datos and enlaces is None:
        errores.append(
            ValidationError(ruta_relativa, "enlaces_externos", "no puede ser null")
        )

    if enlaces is not None:
        if not isinstance(enlaces, list):
            errores.append(ValidationError(ruta_relativa, "enlaces_externos", "lista"))
        else:
            for i, e in enumerate(enlaces):
                pref = f"enlaces_externos[{i}]"

                if not isinstance(e, dict):
                    errores.append(ValidationError(ruta_relativa, pref, "objeto"))
                    continue

                extra_e = set(e.keys()) - {"titulo", "url", "tipo"}
                if extra_e:
                    errores.append(
                        ValidationError(ruta_relativa, pref, f"desconocidos: {sorted(extra_e)}")
                    )

                if "titulo" not in e or not isinstance(e["titulo"], str) or not e["titulo"]:
                    errores.append(
                        ValidationError(ruta_relativa, f"{pref}.titulo", "string no vacío")
                    )

                if not _url_http(e.get("url")):
                    errores.append(
                        ValidationError(ruta_relativa, f"{pref}.url", "URL http(s)")
                    )

                if "tipo" in e and not isinstance(e["tipo"], str):
                    errores.append(
                        ValidationError(ruta_relativa, f"{pref}.tipo", "string")
                    )

    # Verificación final: el propio meta.json debe estar en ruta segura.
    ok, motivo = es_ruta_segura(ruta_meta.parent, ruta_meta)

    if not ok:
        errores.append(ValidationError(ruta_relativa, "meta.json", motivo))

    return (
        PaginaMeta(
            ruta_relativa=ruta_relativa,
            ruta_fisica=ruta_meta,
            datos=datos,
            fotos_validadas=fotos_validadas,
        ),
        errores,
    )
