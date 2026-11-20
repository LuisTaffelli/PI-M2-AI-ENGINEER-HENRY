from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingSpec:
    provider: str
    model: str
    revision: str
    dimension: int
    max_tokens: int
    normalized: bool
    query_prefix: str
    document_prefix: str
