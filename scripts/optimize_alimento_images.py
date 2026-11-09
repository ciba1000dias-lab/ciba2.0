#!/usr/bin/env python3
"""Valida las imágenes de la biblioteca sin descargar archivos de Internet.

Las imágenes externas se conservan para que el navegador intente mostrarlas.
Las imágenes locales solo se conservan si el archivo existe dentro de
assets/images/alimentos/. Una imagen ausente se omite individualmente y nunca
debe bloquear la compilación del sitio.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RUTA_LOCAL_PERMITIDA = "assets/images/alimentos/"


def preparar_foto(foto: dict, raiz: Path) -> str:
    """Devuelve 'externa', 'local' o 'omitida', sin solicitudes HTTP."""
    url = foto.get("url", "")
    if not isinstance(url, str) or not url:
        foto["url"] = ""
        foto.pop("variantes", None)
        foto.pop("formato_local", None)
        return "omitida"

    # No descargar ni borrar imágenes externas: conservar su URL original.
    if url.startswith(("https://", "http://")):
        foto.pop("variantes", None)
        foto.pop("formato_local", None)
        return "externa"

    # Solo se permiten rutas relativas dentro del directorio oficial.
    ruta = url.replace("\\", "/")
    if not ruta.startswith(RUTA_LOCAL_PERMITIDA) or ".." in Path(ruta).parts:
        foto["url"] = ""
        foto.pop("variantes", None)
        foto.pop("formato_local", None)
        return "omitida"

    archivo = (raiz / ruta).resolve()
    try:
        archivo.relative_to(raiz.resolve())
    except ValueError:
        foto["url"] = ""
        foto.pop("variantes", None)
        foto.pop("formato_local", None)
        return "omitida"

    if not archivo.is_file():
        foto["url"] = ""
        foto.pop("variantes", None)
        foto.pop("formato_local", None)
        return "omitida"

    foto["url"] = ruta
    foto.pop("variantes", None)
    foto.pop("formato_local", None)
    return "local"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=Path("dist"), help="Directorio publicado del build.")
    parser.add_argument("--pilot", action="store_true", help="Compatibilidad con el antiguo modo piloto.")
    args = parser.parse_args()

    raiz = args.src.resolve()
    directorio = raiz / "assets" / "data" / "alimentos"
    if not directorio.is_dir():
        parser.error(f"No existe el directorio de datos de alimentos: {directorio}")

    archivos = sorted(directorio.glob("*.json"))
    fichas = 0
    imagenes_locales = 0
    imagenes_externas = 0
    imagenes_omitidas = 0
    errores: list[str] = []

    for archivo in archivos:
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
            alimentos = datos.get("alimentos", [])
            if not isinstance(alimentos, list):
                raise ValueError("El campo 'alimentos' no es una lista.")

            for alimento in alimentos:
                if not isinstance(alimento, dict):
                    continue
                fichas += 1
                fotos = []
                if isinstance(alimento.get("imagen_principal"), dict):
                    fotos.append(alimento["imagen_principal"])
                fotos.extend(
                    foto for foto in alimento.get("imagenes", [])
                    if isinstance(foto, dict)
                )
                for foto in fotos:
                    estado = preparar_foto(foto, raiz)
                    if estado == "local":
                        imagenes_locales += 1
                    elif estado == "externa":
                        imagenes_externas += 1
                    else:
                        imagenes_omitidas += 1

            archivo.write_text(
                json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errores.append(f"{archivo.name}: {exc}")

    if errores:
        print("\n".join(errores))
        return 1

    print(
        f"Biblioteca preparada: {fichas} fichas; "
        f"{imagenes_locales} imágenes locales; "
        f"{imagenes_externas} imágenes externas conservadas; "
        f"{imagenes_omitidas} imágenes ausentes omitidas. "
        "No se realizaron descargas de Internet."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
