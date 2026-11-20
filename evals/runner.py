"""Comando de revisión de etiquetas y evaluación de ambos índices."""

import argparse
import json
from pathlib import Path
import sys


def main(root: Path):
    from evals.contracts.golden import load_golden
    from evals.suite import evaluate
    from nubbix_assist.bootstrap import load_build

    parser = argparse.ArgumentParser(description="Comparar dos estrategias en el mismo golden.")
    parser.add_argument("--builds", nargs=2, required=True, metavar=("BUILD_A", "BUILD_B"))
    parser.add_argument("--dataset", type=Path, default=Path("evals/dataset.jsonl"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-dataset", action="store_true", help="Verificar las etiquetas y contar los borradores.")
    mode.add_argument("--retrieve-only", action="store_true", help="Medir recuperación sin usar las APIs.")
    parser.add_argument("--max-calls", type=int, default=0, help="Presupuesto total de llamadas de generación y juez.")
    args = parser.parse_args()
    try:
        builds = [load_build(root, name) for name in args.builds]
        dataset = root / args.dataset
        rows = load_golden(dataset, root, builds, require_review=not args.check_dataset)
        if args.check_dataset:
            print(json.dumps({"questions": len(rows), "draft": sum(r["labeling_status"] == "draft" for r in rows)}))
            return
        if not args.retrieve_only and args.max_calls < 1:
            parser.error("La evaluación completa requiere un --max-calls positivo.")
        report = evaluate(root, builds, dataset, rows, retrieval_only=args.retrieve_only, max_calls=args.max_calls)
        print(json.dumps({"run_id": report["run_id"], "calls": report["calls_used"],
                          "strategies": {k: v["summary"] for k, v in report["strategies"].items()}}, indent=2))
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(project_root / "src"), str(project_root)]
    main(project_root)
