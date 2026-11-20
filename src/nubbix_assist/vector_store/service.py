from .contracts.provider import VectorIndex
from .errors import IndexError


def verify_ids(index: VectorIndex, expected: set[str]) -> None:
    if index.ids() != expected:
        raise IndexError("Los IDs de Chroma difieren de los del catálogo.")
