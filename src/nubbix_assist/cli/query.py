"""Entrada de consulta independiente de la construcción de índices."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from nubbix_assist.bootstrap import make_retriever


def main():
    parser = argparse.ArgumentParser(description="Consultar un índice publicado de Nubbix.")
    parser.add_argument("question")
    parser.add_argument("--build", required=True)
    parser.add_argument("--source", help="Ruta relativa de un documento para filtrar ambas ramas.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    try:
        retriever = make_retriever(root, args.build)
        result = retriever.retrieve(args.question, source=args.source)
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
