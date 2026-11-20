from typing import Literal, Protocol

from .inputs import TextInput
from .outputs import EmbeddedText
from .spec import EmbeddingSpec

Role = Literal["query", "document"]


class EmbeddingProvider(Protocol):
    spec: EmbeddingSpec

    def encode(self, inputs: list[TextInput], role: Role) -> list[EmbeddedText]: ...
