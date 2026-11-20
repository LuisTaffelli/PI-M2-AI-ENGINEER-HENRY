from dataclasses import dataclass
from nubbix_assist.chunking.contracts import Chunk


@dataclass(frozen=True)
class Selected:
    chunk: Chunk
    score: float


@dataclass
class Retrieval:
    question: str
    build_id: str
    config: dict
    vector_candidates: list[tuple[str, float]]
    lexical_candidates: list[tuple[str, float]]
    selected: list[Selected]
    elapsed_ms: float
    warnings: list[str]
