from math import isfinite

from .errors import IndexError


def validate_vector(vector: list[float], dimension: int) -> None:
    if len(vector) != dimension or not all(map(isfinite, vector)) or not any(vector):
        raise IndexError("El vector no es compatible con la dimensión o métrica del índice.")
