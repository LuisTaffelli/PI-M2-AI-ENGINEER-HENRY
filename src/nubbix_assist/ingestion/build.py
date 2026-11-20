"""Construcción de una versión aislada y publicación del manifest como último paso."""

from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
from uuid import uuid4

from nubbix_assist.artifacts.catalog import read_catalog, write_catalog
from nubbix_assist.artifacts.contracts.manifest import Manifest
from nubbix_assist.artifacts.validators import digest, file_digest, validate_build
from nubbix_assist.embeddings.contracts.inputs import TextInput
from nubbix_assist.lexical.index import BM25Index
from nubbix_assist.vector_store.contracts.inputs import VectorRecord
from nubbix_assist.vector_store.contracts.spec import IndexSpec
from .service import inspect_document


def build_index(root: Path, name: str, strategy, embeddings, open_vectors) -> Manifest:
    sources = {}
    chunks = []
    provenance = json.loads((root / "docs/fuentes/procedencia.json").read_text())["corpus"]["files"]
    for item in sorted(provenance, key=lambda item: item["path"]):
        source = item["path"]
        batch = inspect_document(Path(source), project_root=root, strategy=strategy)
        if batch[0].source_sha256 != item["sha256"]:
            raise ValueError(f"El original de {source} difiere de su procedencia registrada.")
        sources[source] = batch[0].source_sha256
        chunks.extend(batch)
    if not chunks:
        raise ValueError("El corpus está vacío.")
    ids = [chunk.chunk_id for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("El catálogo contiene IDs duplicados.")
    build_id = f"{name}-{uuid4().hex}"
    directory = root / "data/indexes" / build_id
    directory.mkdir(parents=True, exist_ok=False)
    spec = IndexSpec(embeddings.spec.dimension, digest(asdict(embeddings.spec)))
    vectors = open_vectors(directory / "chroma", spec, create=True)
    for offset in range(0, len(chunks), 32):
        batch = chunks[offset:offset + 32]
        outputs = embeddings.encode([TextInput(c.chunk_id, c.content) for c in batch], "document")
        vectors.write([VectorRecord(c.chunk_id, out.vector, c.source, c.section_paths, name)
                       for c, out in zip(batch, outputs, strict=True)])
    write_catalog(directory / "chunks.jsonl", chunks)
    lexical = BM25Index.build(chunks)
    (directory / "bm25.json").write_text(json.dumps(asdict(lexical), ensure_ascii=False), encoding="utf-8")
    manifest = Manifest(
        1, build_id, datetime.now(timezone.utc).isoformat(), "ready", name, chunks[0].strategy_fingerprint,
        sources, digest(sources), embeddings.spec, spec, len(ids), digest(sorted(ids)),
        {file: file_digest(directory / file) for file in ("chunks.jsonl", "bm25.json")},
        {package: version(package) for package in ("chromadb", "sentence-transformers", "torch", "transformers")})
    reopened = open_vectors(directory / "chroma", spec, create=False)
    validate_build(manifest, read_catalog(directory / "chunks.jsonl"),
                   BM25Index(**json.loads((directory / "bm25.json").read_text())), reopened)
    temp = directory / "manifest.tmp"
    temp.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(directory / "manifest.json")
    return manifest
