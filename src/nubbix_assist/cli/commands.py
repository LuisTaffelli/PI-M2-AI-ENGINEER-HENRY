"""Inspección de los chunks de un documento desde la consola."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from nubbix_assist.bootstrap import STRATEGIES
from nubbix_assist.ingestion.service import inspect_document


def ingest_cli(project_root: Path) -> None:
    parser = argparse.ArgumentParser(description="Ingesta del corpus de Nubbix.")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Mostrar los chunks como JSON.")
    inspect.add_argument("source", type=Path, help="Ruta del Markdown relativa al proyecto.")
    inspect.add_argument("--section", help="Mostrar solo los chunks con este título de sección.")
    inspect.add_argument("--strategy", choices=STRATEGIES, default="headings_v1")
    args = parser.parse_args()

    try:
        chunks = inspect_document(args.source, project_root=project_root, strategy=STRATEGIES[args.strategy])
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    if args.section is not None:
        chunks = [chunk for chunk in chunks if args.section in chunk.section_paths]
        if not chunks:
            parser.exit(1, f"No se encontró la sección «{args.section}» en {args.source}.\n")
    print(json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=False, indent=2))
