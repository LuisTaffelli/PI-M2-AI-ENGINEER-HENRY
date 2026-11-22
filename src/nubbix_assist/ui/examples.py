"""Respuestas versionadas de la evaluación y sus pasajes en el corpus original."""
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import re

from nubbix_assist.bootstrap import STRATEGIES
from nubbix_assist.chunking.contracts import Chunk
from nubbix_assist.generation.validators import validate_answer
from nubbix_assist.ingestion.service import inspect_document


@dataclass
class SavedQuestion:
    question: str
    versions: dict[str, tuple[str, list[Chunk]]] = field(default_factory=dict)


def load_examples(root: Path) -> dict[str, SavedQuestion]:
    folder = root / "evals/resultados"
    with (folder / "2026-11-22-generacion-golden-revisado.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    catalogs = {}
    for strategy in {row["estrategia"] for row in rows}:
        catalogs[strategy] = {
            chunk.chunk_id: chunk
            for source in sorted((root / "data/corpus").glob("*.md"))
            for chunk in inspect_document(source.relative_to(root), project_root=root, strategy=STRATEGIES[strategy])
        }

    saved = {}
    for row in rows:
        qid, strategy, text = row["pregunta_id"], row["estrategia"], row["respuesta"]
        item = saved.setdefault(qid, SavedQuestion(row["pregunta"]))
        if item.question != row["pregunta"] or strategy in item.versions:
            raise ValueError(f"Ejemplo guardado ambiguo para {qid}.")
        ids = list(dict.fromkeys(re.findall(r"\[([0-9a-f]{64})\]", text)))
        catalog = catalogs[strategy]
        validate_answer({"system_answer": text, "cited_chunk_ids": ids}, catalog.keys())
        item.versions[strategy] = text, [catalog[key] for key in ids]

    pilot = json.loads((folder / "2026-11-22-ejemplo-q09.json").read_text(encoding="utf-8"))
    if pilot["user_question"] != saved["q09"].question:
        raise ValueError("La pregunta del piloto difiere de la pregunta de capacitación.")
    catalog = catalogs["headings_v1"]
    ids = [c["chunk_id"] for c in pilot["chunks_related"]]
    validate_answer({"system_answer": pilot["system_answer"], "cited_chunk_ids": ids}, catalog.keys())
    saved["q09"].versions["pilot"] = pilot["system_answer"], [catalog[key] for key in ids]
    return saved
