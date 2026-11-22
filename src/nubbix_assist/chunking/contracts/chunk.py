"""Registro canónico de un fragmento y su ubicación en el original."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source: str
    source_sha256: str
    strategy: str
    strategy_fingerprint: str
    start_char: int
    end_char: int
    section_paths: tuple[str, ...]
    body: str
    content: str
    content_sha256: str
    ordinal: int
    version: str = "1"
