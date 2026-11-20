from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddedText:
    id: str
    vector: list[float]
