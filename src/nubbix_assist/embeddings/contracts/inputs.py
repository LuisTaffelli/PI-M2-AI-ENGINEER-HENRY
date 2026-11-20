from dataclasses import dataclass


@dataclass(frozen=True)
class TextInput:
    id: str
    text: str
