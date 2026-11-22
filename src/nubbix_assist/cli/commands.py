"""Inspección de los chunks de un documento desde la consola."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from nubbix_assist.bootstrap import STRATEGIES, build, prepare_local_model
from nubbix_assist.ingestion.service import inspect_document
from nubbix_assist.ingestion.revisions import register_version


def ingest_cli(project_root: Path) -> None:
    parser = argparse.ArgumentParser(description="Ingesta del corpus de Nubbix.")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Mostrar los chunks como JSON.")
    inspect.add_argument("source", type=Path, help="Ruta del Markdown relativa al proyecto.")
    inspect.add_argument("--section", help="Mostrar solo los chunks con este título de sección.")
    inspect.add_argument("--strategy", choices=STRATEGIES, default="headings_v1")
    inspect.add_argument("--version", help="Versión del documento. Por defecto usa la última registrada.")
    register = commands.add_parser("add-version", help="Registrar una copia editada con el número de versión que elijas.")
    register.add_argument("source", type=Path, help="Ruta del documento original en data/corpus/.")
    register.add_argument("--version", required=True, help="Número de la nueva revisión, por ejemplo 2, 1.10 o 3.4.2.")
    register.add_argument("--file", required=True, type=Path, help="Markdown editado que se va a registrar.")
    commands.add_parser("prepare-model", help="Descargar la revisión configurada de E5 a la caché local.")
    commands.add_parser("prepare-reranker", help="Descargar el cross-encoder opcional a la caché local.")
    build_parser = commands.add_parser("build", help="Construir y verificar un índice local.")
    build_parser.add_argument("--strategy", required=True, choices=STRATEGIES)
    args = parser.parse_args()

    try:
        if args.command == "add-version":
            path = register_version(project_root, args.source, args.file, args.version)
            print(json.dumps({"version": args.version, "path": str(path.relative_to(project_root))}, ensure_ascii=False))
            return
        if args.command == "prepare-reranker":
            from nubbix_assist.retrieval.rerank import prepare_reranker
            print(json.dumps({"snapshot": prepare_reranker()}, ensure_ascii=False))
            return
        if args.command == "prepare-model":
            print(json.dumps({"snapshot": prepare_local_model(project_root)}, ensure_ascii=False))
            return
        if args.command == "build":
            print(json.dumps(asdict(build(project_root, args.strategy)), ensure_ascii=False, indent=2))
            return
        chunks = inspect_document(args.source, project_root=project_root, strategy=STRATEGIES[args.strategy],
                                  version=args.version)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    if args.section is not None:
        chunks = [chunk for chunk in chunks if args.section in chunk.section_paths]
        if not chunks:
            parser.exit(1, f"No se encontró la sección «{args.section}» en {args.source}.\n")
    print(json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=False, indent=2))
