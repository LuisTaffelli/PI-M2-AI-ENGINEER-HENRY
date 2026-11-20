"""Lectura y segmentación de un documento antes de indexarlo."""

from pathlib import Path

from nubbix_assist.chunking.contracts import Chunk, ChunkStrategy
from nubbix_assist.chunking.validators import validate_chunks

from .markdown_loader import load_markdown


def inspect_document(source: Path, *, project_root: Path, strategy: ChunkStrategy) -> list[Chunk]:
    document = load_markdown(source, project_root=project_root)
    chunks = strategy(document)
    validate_chunks(document, chunks)
    return chunks
