"""Audita enlaces locales del sitio CIBA ya construido.

No consulta destinos externos. Comprueba archivos, rutas de directorio y
fragmentos HTML locales. Uso:
    python scripts/audit_internal_links.py --root dist
    python scripts/audit_internal_links.py --root dist --strict
"""
from __future__ import annotations

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, int]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        for attr in ("href", "src", "poster", "action"):
            value = values.get(attr)
            if value:
                self.links.append((value.strip(), self.getpos()[0]))
        ident = values.get("id")
        if ident:
            self.ids.add(ident)
        if tag.lower() == "a" and values.get("name"):
            self.ids.add(values["name"])


def _leer_html(path: Path) -> _Links:
    parser = _Links()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()
    return parser


def auditar(root: Path, base_url: str | None = None) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"No existe la carpeta de publicación: {root}")

    base = urlsplit(base_url or "")
    base_path = base.path.rstrip("/")
    paginas = sorted(root.rglob("*.html"))
    cache: dict[Path, _Links] = {}
    errores: list[dict] = []
    revisados = 0
    externos = 0

    for pagina in paginas:
        try:
            origen = _leer_html(pagina)
        except OSError as exc:
            errores.append({"archivo": pagina.relative_to(root).as_posix(), "linea": 0,
                            "destino": "", "motivo": f"No se pudo leer HTML: {exc}"})
            continue
        cache[pagina] = origen

    for pagina, parser in cache.items():
        rel_origen = pagina.relative_to(root).as_posix()
        for raw, linea in parser.links:
            if not raw or raw.startswith("#"):
                if raw.startswith("#") and len(raw) > 1:
                    fragmento = unquote(raw[1:])
                    revisados += 1
                    if fragmento not in parser.ids:
                        errores.append({"archivo": rel_origen, "linea": linea,
                                        "destino": raw, "motivo": "Fragmento no encontrado"})
                continue

            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme in ("http", "https") and base.hostname and parsed.hostname == base.hostname:
                    ruta_url = unquote(parsed.path)
                    if base_path and (ruta_url == base_path or ruta_url.startswith(base_path + "/")):
                        ruta_url = ruta_url[len(base_path):] or "/"
                    else:
                        externos += 1
                        continue
                else:
                    externos += 1
                    continue
            else:
                ruta_url = unquote(parsed.path)
                if base_path and (ruta_url == base_path or ruta_url.startswith(base_path + "/")):
                    ruta_url = ruta_url[len(base_path):] or "/"

            if not ruta_url:
                destino = pagina
            elif ruta_url.startswith("/"):
                destino = root / ruta_url.lstrip("/")
            else:
                destino = pagina.parent / ruta_url

            try:
                destino = destino.resolve()
                destino.relative_to(root)
            except (OSError, ValueError):
                revisados += 1
                errores.append({"archivo": rel_origen, "linea": linea,
                                "destino": raw, "motivo": "La ruta sale del sitio publicado"})
                continue

            if destino.is_dir():
                destino = destino / "index.html"
            elif not destino.suffix and not destino.exists():
                candidato = destino / "index.html"
                if candidato.is_file():
                    destino = candidato

            revisados += 1
            if not destino.is_file():
                errores.append({"archivo": rel_origen, "linea": linea,
                                "destino": raw, "motivo": "Archivo o ruta no encontrado"})
                continue

            fragmento = unquote(parsed.fragment)
            if fragmento and destino.suffix.lower() == ".html":
                if destino not in cache:
                    try:
                        cache[destino] = _leer_html(destino)
                    except OSError:
                        cache[destino] = _Links()
                if fragmento not in cache[destino].ids:
                    errores.append({"archivo": rel_origen, "linea": linea,
                                    "destino": raw, "motivo": "Fragmento no encontrado en destino"})

    return {
        "paginas_html": len(paginas),
        "enlaces_locales_revisados": revisados,
        "enlaces_externos_omitidos": externos,
        "errores": errores,
        "total_errores": len(errores),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audita enlaces locales del sitio CIBA.")
    parser.add_argument("--root", type=Path, default=Path("dist"))
    parser.add_argument("--base-url", default=None,
                        help="URL base del sitio, por ejemplo https://usuario.github.io/ciba2.0/")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--strict", action="store_true",
                        help="Devuelve código distinto de cero si encuentra errores.")
    args = parser.parse_args(argv)

    try:
        resultado = auditar(args.root, args.base_url)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    resumen = (
        f"Auditoría de enlaces: {resultado['paginas_html']} páginas HTML; "
        f"{resultado['enlaces_locales_revisados']} enlaces locales revisados; "
        f"{resultado['enlaces_externos_omitidos']} externos omitidos; "
        f"{resultado['total_errores']} incidencias."
    )
    print(resumen)
    for error in resultado["errores"][:100]:
        print(f"- {error['archivo']}:{error['linea']} -> {error['destino']} [{error['motivo']}]")
    if resultado["total_errores"] > 100:
        print(f"... y {resultado['total_errores'] - 100} incidencias adicionales.")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Informe JSON: {args.json_out}")

    return 1 if args.strict and resultado["total_errores"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
