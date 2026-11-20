from dataclasses import dataclass
import json
from pathlib import Path

from nubbix_assist.chunking.contracts import Chunk
from nubbix_assist.lexical.index import BM25Index
from nubbix_assist.vector_store.contracts.provider import VectorIndex
from .catalog import read_catalog
from .contracts.manifest import Manifest
from .validators import file_digest, validate_build


@dataclass
class Build:
    manifest: Manifest
    catalog: dict[str, Chunk]
    lexical: BM25Index
    vectors: VectorIndex


def open_build(root: Path, build_id: str, open_vectors) -> Build:
    if not build_id or Path(build_id).name != build_id or build_id in {".", ".."}:
        raise ValueError("Identificador de build inválido.")
    directory = root / "data/indexes" / build_id
    manifest = Manifest.parse(json.loads((directory / "manifest.json").read_text()))
    if manifest.build_id != build_id or manifest.state != "ready":
        raise ValueError("El build solicitado no está publicado.")
    for name in ("chunks.jsonl", "bm25.json"):
        if manifest.files[name] != file_digest(directory / name):
            raise ValueError(f"Falló la verificación de {name}.")
    catalog = read_catalog(directory / "chunks.jsonl")
    lexical = BM25Index(**json.loads((directory / "bm25.json").read_text()))
    vectors = open_vectors(directory / "chroma", manifest.vector_store, create=False)
    validate_build(manifest, catalog, lexical, vectors)
    return Build(manifest, catalog, lexical, vectors)
