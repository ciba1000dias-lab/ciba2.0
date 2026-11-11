#!/usr/bin/env bash
# Construcción reproducible de CIBA para Cloudflare Pages.
set -Eeuo pipefail

echo "== CIBA: dependencias =="
python -m pip install --disable-pip-version-check numpy imageio-ffmpeg mutagen

echo "== CIBA: pruebas =="
python -m unittest discover -s tests -t . -v

echo "== CIBA: sintaxis JavaScript =="
node --input-type=module --check < assets/js/ciba-recetario-motor.js
node --input-type=module --check < assets/js/ciba-recetario.js
node --input-type=module --check < assets/js/ciba-global.js
node --check assets/js/ciba-plataforma.js

echo "== CIBA: validación editorial =="
python scripts/validate_content.py --src content

echo "== CIBA: generación del sitio =="
python scripts/build_catalog.py --src content --out dist

echo "== CIBA: generación de podcasts =="
python scripts/build_podcast_c4_10.py --out dist/c/C4/C4-10/podcast-c4-10.mp3
python scripts/build_podcast_c4_11.py --out dist/c/C4/C4-11/podcast-c4-11.mp3
python scripts/build_podcast_c4_12.py --out dist/c/C4/C4-12/podcast-c4-12.mp3

echo "== CIBA: preparación de imágenes =="
python scripts/optimize_alimento_images.py --src dist

echo "== CIBA: build terminado =="
