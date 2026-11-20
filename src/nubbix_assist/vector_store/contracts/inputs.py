from dataclasses import dataclass


@dataclass(frozen=True)
class VectorRecord:
    id: str
    vector: list[float]
    source: str
    sections: tuple[str, ...]
    strategy: str
