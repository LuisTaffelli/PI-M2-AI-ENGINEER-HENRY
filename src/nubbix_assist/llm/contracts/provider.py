from typing import Protocol
from .inputs import Request
from .outputs import Completion


class Provider(Protocol):
    name: str
    model: str

    def complete(self, request: Request) -> Completion: ...
