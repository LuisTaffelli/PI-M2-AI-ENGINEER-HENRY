from dataclasses import dataclass


@dataclass(frozen=True)
class VectorHit:
    id: str
    distance: float
