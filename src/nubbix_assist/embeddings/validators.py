from math import isclose, isfinite, sqrt

from .contracts.inputs import TextInput
from .contracts.outputs import EmbeddedText
from .contracts.spec import EmbeddingSpec
from .errors import EmbeddingError


def validate_inputs(inputs: list[TextInput]) -> None:
    if not inputs or any(not item.id or not item.text.strip() for item in inputs):
        raise EmbeddingError("Se requieren IDs y textos no vacíos.")
    if len({item.id for item in inputs}) != len(inputs):
        raise EmbeddingError("El lote de embeddings contiene IDs duplicados.")


def validate_outputs(inputs: list[TextInput], outputs: list[EmbeddedText], spec: EmbeddingSpec) -> None:
    if [item.id for item in inputs] != [item.id for item in outputs]:
        raise EmbeddingError("El proveedor cambió la cantidad o el orden de IDs.")
    for item in outputs:
        vector = item.vector
        if len(vector) != spec.dimension or not all(map(isfinite, vector)):
            raise EmbeddingError(f"Dimensión o valores inválidos para {item.id}.")
        norm = sqrt(sum(value * value for value in vector))
        if not norm or (spec.normalized and not isclose(norm, 1.0, abs_tol=1e-4)):
            raise EmbeddingError(f"Norma incompatible para {item.id}.")
