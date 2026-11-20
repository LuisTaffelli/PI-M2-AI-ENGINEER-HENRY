from dataclasses import dataclass


@dataclass(frozen=True)
class Completion:
    text: str
    usage: dict
    finish: str
