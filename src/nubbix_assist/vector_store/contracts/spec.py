from dataclasses import dataclass


@dataclass(frozen=True)
class IndexSpec:
    dimension: int
    embedding_fingerprint: str
    metric: str = "cosine"
