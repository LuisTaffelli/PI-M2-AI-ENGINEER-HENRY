"""Ventanas de palabras con offsets del documento y contexto de las secciones alcanzadas."""

import re

from nubbix_assist.chunking.contracts import Chunk
from nubbix_assist.chunking.factory import fingerprint, make_chunk
from nubbix_assist.chunking.sections import section_headings
from nubbix_assist.ingestion.contracts import Document


def chunk_by_words(document: Document, *, size: int = 80, overlap: int = 20) -> list[Chunk]:
    if not 0 <= overlap < size:
        raise ValueError("La ventana debe ser positiva y el solapamiento menor que su tamaño.")
    words = list(re.finditer(r"\S+", document.raw_text))
    headings = list(section_headings(document))
    boundaries = [start for start, _, _ in headings[1:]] + [len(document.raw_text)]
    sections = [(start, end, label) for (start, _, label), end in zip(headings, boundaries)]
    rule = fingerprint({"strategy": "words_v1", "size": size, "overlap": overlap,
                        "context": "title_sections_body_v1"})
    chunks = []
    for first in range(0, len(words), size - overlap):
        stop = min(first + size, len(words))
        start, end = words[first].start(), words[stop - 1].end()
        labels = tuple(label for left, right, label in sections if left < end and start < right)
        chunks.append(make_chunk(document, strategy="words_v1", strategy_fingerprint=rule,
                                 start_char=start, end_char=end, section_paths=labels,
                                 ordinal=len(chunks) + 1))
        if stop == len(words):
            break
    return chunks
