"""Entrada local para inspeccionar el corpus antes de construir el índice."""

from pathlib import Path
import sys


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root / "src"))
    from nubbix_assist.cli.commands import ingest_cli

    ingest_cli(project_root)
