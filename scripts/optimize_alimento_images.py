#!/usr/bin/env python3
"""Optimiza un piloto de fotografías de alimentos a WebP durante el build.

Las fuentes originales y los metadatos de autoría/licencia permanecen en los
JSON versionados. Solo se transforman copias dentro de dist/.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

ANCHORES = (320, 640, 960)
PILOTO = {
    "frutas": {"aguacate"},
    "viandas": {"boniato"},
    "vegetales": {"calabaza"},
}
MAX_BYTES = 20 * 1024 * 1024
USER_AGENT = "CIBA-Alimentos-ImageOptimizer/1.0 (GitHub Actions build)"


def descargar(url: str) -> bytes:
    if not isinstance(url, str) or not url.startswith(("https://upload.wikimedia.org/", "https://thumb.wikimedia.org/", "https://commons.wikimedia.org/")):
        raise ValueError(f"Fuente de imagen no autorizada: {url!r}")
    solicitud = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(solicitud, timeout=45) as respuesta:
        tipo = respuesta.headers.get("Content-Type", "")
        datos = respuesta.read(MAX_BYTES + 1)
    if len(datos) > MAX_BYTES:
        raise ValueError("La imagen supera el límite de 20 MB.")
    if not tipo.lower().startswith("image/"):
        raise ValueError(f"La URL no devolvió una imagen (Content-Type: {tipo or 'desconocido'}).")
    return datos


def convertir(datos: bytes, destino_base: Path) -> dict[str, str]:
    with Image.open(io.BytesIO(datos)) as original:
        imagen = ImageOps.exif_transpose(original)
        if imagen.width < 1 or imagen.height < 1:
            raise ValueError("Dimensiones de imagen inválidas.")
        perfil = imagen.info.get("icc_profile")
        if imagen.mode not in ("RGB", "RGBA"):
            imagen = imagen.convert("RGBA" if "transparency" in imagen.info else "RGB")
        elif imagen.mode == "RGBA":
            imagen = imagen.copy()
        else:
            imagen = imagen.copy()

        variantes: dict[str, str] = {}
        for ancho in ANCHORES:
            copia = imagen.copy()
            copia.thumbnail((ancho, ancho), Image.Resampling.LANCZOS)
            destino = destino_base.parent / f"{destino_base.name}-{ancho}.webp"
            destino.parent.mkdir(parents=True, exist_ok=True)
            opciones = {"format": "WEBP", "quality": 82, "method": 6}
            if perfil:
                opciones["icc_profile"] = perfil
            copia.save(destino, **opciones)
            variantes[str(ancho)] = destino.relative_to(destino_base.parents[3]).as_posix()
        return variantes


def optimizar_foto(foto: dict, destino_base: Path) -> None:
    url_original = foto.get("url_original") or foto.get("url")
    if not url_original:
        raise ValueError("La fotografía no tiene URL de origen.")
    datos = descargar(url_original)
    variantes = convertir(datos, destino_base)
    foto["url_original"] = url_original
    foto["url"] = variantes["960"]
    foto["variantes"] = variantes
    foto["formato_local"] = "WebP"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=Path("dist"), help="Directorio publicado del build.")
    parser.add_argument("--pilot", action="store_true", help="Procesa solo aguacate, boniato y calabaza.")
    args = parser.parse_args()

    raiz = args.src.resolve()
    if not raiz.is_dir():
        parser.error(f"No existe el directorio de publicación: {raiz}")

    grupos = sorted(PILOTO) if args.pilot else sorted(p.stem for p in (raiz / "assets/data/alimentos").glob("*.json"))
    procesadas = 0
    errores: list[str] = []

    for grupo in grupos:
        archivo = raiz / "assets" / "data" / "alimentos" / f"{grupo}.json"
        if not archivo.is_file():
            if args.pilot:
                errores.append(f"No existe el grupo del piloto: {archivo}")
            continue
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errores.append(f"{archivo}: {exc}")
            continue

        alimentos = datos.get("alimentos", [])
        ids_piloto = PILOTO.get(grupo, set()) if args.pilot else None
        encontrados: set[str] = set()

        for alimento in alimentos:
            alimento_id = alimento.get("id", "")
            if ids_piloto is not None and alimento_id not in ids_piloto:
                continue
            fotos = []
            if alimento.get("imagen_principal"):
                fotos.append(("principal", alimento["imagen_principal"]))
            fotos.extend((f"imagen-{i:02d}", foto) for i, foto in enumerate(alimento.get("imagenes", []), 1))

            for etiqueta, foto in fotos:
                try:
                    if not re.fullmatch(r"[a-z0-9-]+", alimento_id):
                        raise ValueError(f"Identificador inseguro: {alimento_id!r}")
                    destino = raiz / "assets" / "img" / "alimentos" / grupo / f"{alimento_id}-{etiqueta}"
                    optimizar_foto(foto, destino)
                    procesadas += 1
                except Exception as exc:
                    errores.append(f"{grupo}/{alimento_id}/{etiqueta}: {exc}")
            encontrados.add(alimento_id)

        if ids_piloto is not None:
            faltantes = ids_piloto - encontrados
            if faltantes:
                errores.append(f"{grupo}: no se encontraron alimentos del piloto: {', '.join(sorted(faltantes))}")

        if not errores:
            archivo.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errores:
        print("\n".join(errores), file=sys.stderr)
        return 1
    print(f"Fotografías convertidas a WebP: {procesadas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
