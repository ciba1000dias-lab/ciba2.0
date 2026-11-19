#!/usr/bin/env python3
"""Genera la versión PDF A4 de la cartilla SVG aprobada, sin redibujarla."""
from pathlib import Path
import argparse
import cairosvg

parser = argparse.ArgumentParser()
parser.add_argument("--src", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()

source = Path(args.src)
output = Path(args.out)
if not source.is_file():
    raise SystemExit(f"No se encontró el SVG fuente: {source}")
output.parent.mkdir(parents=True, exist_ok=True)

# A4 en puntos convertido a píxeles CSS (96 dpi); se conserva el vector.
cairosvg.svg2pdf(
    url=str(source),
    write_to=str(output),
    output_width=793.7008,
    output_height=1122.5197,
)
if not output.is_file() or output.stat().st_size < 5000:
    raise SystemExit("El PDF generado está ausente o incompleto")
print(f"Cartilla PDF creada: {output} ({output.stat().st_size} bytes)")
