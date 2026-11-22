"""Validación del golden y de sus referencias antes de medir o llamar a modelos."""

from hashlib import sha256
import json
from pathlib import Path


def reviewed_for(row: dict, builds: list) -> bool:
    """Indica si la pregunta y las etiquetas de todas las estrategias elegidas están revisadas."""
    approved = row.get("reviewed_strategies", row["expected_chunks"])
    return row["labeling_status"] == "reviewed" and all(
        build.manifest.strategy_fingerprint in approved for build in builds
    )


def load_golden(path: Path, root: Path, builds: list, *, require_review: bool) -> list[dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    ids = [r["question_id"] for r in records]
    if len(records) < 25 or len(set(ids)) != len(ids) or not all(ids):
        raise ValueError("Se requieren al menos 25 preguntas con IDs únicos.")
    manifests = [build.manifest for build in builds]
    if len(manifests) < 2 or len({m.strategy for m in manifests}) != len(manifests):
        raise ValueError("Elegí al menos dos estrategias distintas para la comparación.")
    first = manifests[0]
    if any(m.corpus_fingerprint != first.corpus_fingerprint or m.embeddings != first.embeddings
           for m in manifests[1:]):
        raise ValueError("La comparación requiere el mismo corpus y espacio de embeddings.")
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
        if "reviewed_strategies" in row:
            approved = row["reviewed_strategies"]
            if not isinstance(approved, list) or any(
                not isinstance(key, str) or key not in row["expected_chunks"] for key in approved
            ):
                raise ValueError(f"{label}: las estrategias revisadas deben tener etiquetas en el golden.")
        if require_review and not reviewed_for(row, builds):
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
