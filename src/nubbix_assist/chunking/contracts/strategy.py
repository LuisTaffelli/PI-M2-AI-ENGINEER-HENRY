"""Una estrategia transforma un documento en chunks ordenados."""

from typing import Protocol

from nubbix_assist.ingestion.contracts import Document

from .chunk import Chunk


class ChunkStrategy(Protocol):
    def __call__(self, document: Document) -> list[Chunk]: ...
