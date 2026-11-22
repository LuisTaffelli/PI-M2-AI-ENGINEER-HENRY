from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from nubbix_assist.lexical.validators import validate as validate_bm25
from nubbix_assist.vector_store.service import verify_ids


def digest(value) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()


def file_digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def corpus_digest(sources: dict, source_versions: dict) -> str:
    # Conserva la huella del corpus original usada por las evaluaciones publicadas.
    if all(label == "1" for label in source_versions.values()):
        return digest(sources)
    return digest({"sources": sources, "source_versions": source_versions})


def validate_build(manifest, catalog, lexical, vectors) -> None:
    ids = set(catalog)
    if (manifest.schema_version not in (1, 2) or manifest.state != "ready" or not ids
            or manifest.count != len(ids) or digest(sorted(ids)) != manifest.ids_sha256
            or manifest.sources.keys() != manifest.source_versions.keys()
            or corpus_digest(manifest.sources, manifest.source_versions) != manifest.corpus_fingerprint
            or digest(asdict(manifest.embeddings)) != manifest.vector_store.embedding_fingerprint):
        raise ValueError("Manifest incompatible con el catálogo o con el espacio de embeddings.")
    for chunk in catalog.values():
        if (manifest.sources.get(chunk.source) != chunk.source_sha256 or chunk.strategy != manifest.strategy
                or manifest.source_versions.get(chunk.source) != chunk.version
                or chunk.strategy_fingerprint != manifest.strategy_fingerprint):
            raise ValueError("La procedencia del chunk difiere del manifest.")
    validate_bm25(lexical, ids)
    verify_ids(vectors, ids)
