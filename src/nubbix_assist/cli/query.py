"""Entrada de consulta independiente de la construcción de índices."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from nubbix_assist.bootstrap import make_retriever, language_model
from nubbix_assist.generation.prompts import load_prompt
from nubbix_assist.llm.service import CallBudget
from nubbix_assist.query.service import answer_retrieval


def main():
    parser = argparse.ArgumentParser(description="Consultar un índice publicado de Nubbix.")
    parser.add_argument("question")
    parser.add_argument("--build", required=True)
    parser.add_argument("--source", help="Ruta relativa de un documento para filtrar ambas ramas.")
    parser.add_argument("--retrieve-only", action="store_true", help="Mostrar rankings y contexto sin llamar a una API.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    try:
        retriever = make_retriever(root, args.build)
        result = retriever.retrieve(args.question, source=args.source)
        if args.retrieve_only:
            output = result
        else:
            model = language_model(root, "GENERATOR", CallBudget(2))
            output = answer_retrieval(root, result, model, load_prompt(root, "generation")).answer
        print(json.dumps(asdict(output), ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
