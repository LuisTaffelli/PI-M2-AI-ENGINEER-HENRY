"""Validación del golden y de sus referencias antes de medir o llamar a modelos."""

from hashlib import sha256
import json
from pathlib import Path


def load_golden(path: Path, root: Path, builds: list, *, require_review: bool) -> list[dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    ids = [r["question_id"] for r in records]
    if len(records) < 25 or len(set(ids)) != len(ids) or not all(ids):
        raise ValueError("Se requieren al menos 25 preguntas con IDs únicos.")
    first, second = (build.manifest for build in builds)
    if (first.strategy == second.strategy or first.corpus_fingerprint != second.corpus_fingerprint
            or first.embeddings != second.embeddings):
        raise ValueError("La comparación requiere dos estrategias, el mismo corpus y el mismo espacio.")
    sources = {}
    for source, expected in first.sources.items():
        raw = (root / source).read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise ValueError(f"El corpus actual difiere del build en {source}.")
        sources[source] = raw.decode("utf-8")
    for row in records:
        label = row["question_id"]
        if (row["corpus_fingerprint"] != first.corpus_fingerprint or not row["question"].strip()
                or row["labeling_status"] not in {"draft", "reviewed"}
                or type(row["answerable"]) is not bool):
            raise ValueError(f"{label}: registro o versión de corpus inválidos.")
        if require_review and row["labeling_status"] != "reviewed":
            raise ValueError(f"{label}: falta la revisión humana del golden.")
        if bool(row["evidence"]) != row["answerable"] or bool(row["expected_facts"]) != row["answerable"]:
            raise ValueError(f"{label}: faltan hechos o evidencia coherentes con answerable.")
        for evidence in row["evidence"]:
            source, start, end = evidence["source"], evidence["start_char"], evidence["end_char"]
            if (source not in sources or first.sources[source] != evidence["source_sha256"]
                    or not 0 <= start < end <= len(sources[source])
                    or sources[source][start:end] != evidence["excerpt"]):
                raise ValueError(f"{label}: la evidencia difiere del original.")
        for build in builds:
            expected = row["expected_chunks"].get(build.manifest.strategy_fingerprint)
            if (not isinstance(expected, list) or bool(expected) != row["answerable"]
                    or len(set(expected)) != len(expected) or not set(expected) <= build.catalog.keys()):
                raise ValueError(f"{label}: etiquetas inválidas para {build.manifest.strategy}.")
    return records
