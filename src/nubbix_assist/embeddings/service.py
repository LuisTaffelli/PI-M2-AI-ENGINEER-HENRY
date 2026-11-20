from .contracts.inputs import TextInput
from .contracts.outputs import EmbeddedText
from .contracts.provider import EmbeddingProvider, Role
from .validators import validate_inputs, validate_outputs


class Embeddings:
    def __init__(self, provider: EmbeddingProvider):
        self.provider = provider
        self.spec = provider.spec

    def encode(self, inputs: list[TextInput], role: Role) -> list[EmbeddedText]:
        validate_inputs(inputs)
        outputs = self.provider.encode(inputs, role)
        validate_outputs(inputs, outputs, self.spec)
        return outputs
