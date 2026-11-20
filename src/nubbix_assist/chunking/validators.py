"""Validación de los chunks de un documento antes de entregarlos a la ingesta."""

from nubbix_assist.ingestion.contracts import Document

from .contracts import Chunk


def validate_chunks(document: Document, chunks: list[Chunk]) -> None:
    if not chunks:
        raise ValueError(f"{document.source}: la estrategia no produjo chunks.")

    seen = set()
    for chunk in chunks:
        if not chunk.chunk_id or chunk.chunk_id in seen:
            raise ValueError(f"{document.source}: ID de chunk vacío o duplicado.")
        seen.add(chunk.chunk_id)
        if (chunk.source, chunk.source_sha256) != (document.source, document.source_sha256):
            raise ValueError(f"El origen del chunk {chunk.ordinal} difiere del documento.")
        if not 0 <= chunk.start_char < chunk.end_char <= len(document.raw_text):
            raise ValueError(f"{document.source}: intervalo inválido en el chunk {chunk.ordinal}.")
        if not chunk.body.strip() or chunk.body != document.raw_text[chunk.start_char:chunk.end_char]:
            raise ValueError(f"{document.source}: cuerpo vacío o distinto del original en el chunk {chunk.ordinal}.")
