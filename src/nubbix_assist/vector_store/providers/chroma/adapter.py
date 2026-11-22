import json
from pathlib import Path

from ...contracts.inputs import VectorRecord
from ...contracts.outputs import VectorHit
from ...contracts.spec import IndexSpec
from ...errors import IndexError
from ...validators import validate_vector
from .config import COLLECTION
from .validators import validate_collection


class ChromaIndex:
    def __init__(self, path: Path, spec: IndexSpec, *, create: bool):
        import chromadb

        if not create and not (path / "chroma.sqlite3").is_file():
            raise IndexError("Falta la base Chroma del build.")
        self.client = chromadb.PersistentClient(path=str(path))
        self.spec = spec
        if create:
            self.collection = self.client.create_collection(
                COLLECTION, embedding_function=None, configuration={"hnsw": {"space": spec.metric}},
                metadata={"dimension": spec.dimension, "embedding_fingerprint": spec.embedding_fingerprint})
        else:
            self.collection = self.client.get_collection(COLLECTION, embedding_function=None)
        validate_collection(self.collection, spec)

    def write(self, records: list[VectorRecord]) -> None:
        for record in records:
            validate_vector(record.vector, self.spec.dimension)
        self.collection.add(ids=[r.id for r in records], embeddings=[r.vector for r in records],
                            metadatas=[{"source": r.source, "sections": json.dumps(r.sections, ensure_ascii=False),
                                        "strategy": r.strategy, "version": r.version} for r in records])

    def ids(self) -> set[str]:
        return set(self.collection.get(include=[])["ids"])

    def search(self, vector: list[float], limit: int, source: str | None) -> list[VectorHit]:
        validate_vector(vector, self.spec.dimension)
        result = self.collection.query(query_embeddings=[vector], n_results=limit,
                                       where={"source": source} if source else None, include=["distances"])
        hits = [VectorHit(key, distance) for key, distance in zip(result["ids"][0], result["distances"][0], strict=True)]
        return sorted(hits, key=lambda hit: (hit.distance, hit.id))
