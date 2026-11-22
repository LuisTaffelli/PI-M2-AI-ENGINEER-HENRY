"""Ventanas de palabras con offsets del documento y contexto de las secciones alcanzadas."""

import re
from collections.abc import Iterator

from nubbix_assist.chunking.contracts import Chunk
from nubbix_assist.chunking.factory import fingerprint, make_chunk
from nubbix_assist.chunking.sections import section_headings
from nubbix_assist.ingestion.contracts import Document


def word_windows(text: str, start: int, end: int, size: int, overlap: int) -> Iterator[tuple[int, int]]:
    """Divide el intervalo en ventanas y devuelve offsets absolutos sobre el texto original."""
    if not 0 <= overlap < size:
        raise ValueError("La ventana debe ser positiva y el solapamiento menor que su tamaño.")
    words = list(re.compile(r"\S+").finditer(text, start, end))
    for first in range(0, len(words), size - overlap):
        stop = min(first + size, len(words))
        yield words[first].start(), words[stop - 1].end()
        if stop == len(words):
            break


def chunk_by_words(document: Document, *, size: int = 80, overlap: int = 20) -> list[Chunk]:
    headings = list(section_headings(document))
    boundaries = [start for start, _, _ in headings[1:]] + [len(document.raw_text)]
    sections = [(start, end, label) for (start, _, label), end in zip(headings, boundaries)]
    rule = fingerprint({"strategy": "words_v1", "size": size, "overlap": overlap,
                        "context": "title_sections_body_v1"})
    chunks = []
    for start, end in word_windows(document.raw_text, 0, len(document.raw_text), size, overlap):
        labels = tuple(label for left, right, label in sections if left < end and start < right)
        chunks.append(make_chunk(document, strategy="words_v1", strategy_fingerprint=rule,
                                 start_char=start, end_char=end, section_paths=labels,
                                 ordinal=len(chunks) + 1))
    return chunks
