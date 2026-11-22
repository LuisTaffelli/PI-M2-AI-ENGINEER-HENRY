"""Documento tal como se leyó del corpus."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    source: str
    title: str
    source_sha256: str
    raw_text: str
    version: str = "1"
