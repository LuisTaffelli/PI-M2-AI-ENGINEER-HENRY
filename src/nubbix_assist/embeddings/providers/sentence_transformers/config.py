from dataclasses import dataclass


@dataclass(frozen=True)
class LocalModel:
    model: str
    revision: str
    dimension: int
    max_tokens: int
    query_prefix: str
    document_prefix: str
