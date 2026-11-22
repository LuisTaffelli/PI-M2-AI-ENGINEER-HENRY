from dataclasses import dataclass

from nubbix_assist.embeddings.contracts.spec import EmbeddingSpec
from nubbix_assist.vector_store.contracts.spec import IndexSpec


@dataclass(frozen=True)
class Manifest:
    schema_version: int
    build_id: str
    created_at: str
    state: str
    strategy: str
    strategy_fingerprint: str
    sources: dict[str, str]
    corpus_fingerprint: str
    embeddings: EmbeddingSpec
    vector_store: IndexSpec
    count: int
    ids_sha256: str
    files: dict[str, str]
    versions: dict[str, str]
    source_versions: dict[str, str]

    @classmethod
    def parse(cls, data):
        if data["schema_version"] == 1:
            data = {**data, "source_versions": dict.fromkeys(data["sources"], "1")}
        return cls(**{**data, "embeddings": EmbeddingSpec(**data["embeddings"]),
                      "vector_store": IndexSpec(**data["vector_store"])})
