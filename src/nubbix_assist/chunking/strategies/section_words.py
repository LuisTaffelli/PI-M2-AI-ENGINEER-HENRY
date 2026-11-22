"""Ventanas de palabras cuyo solapamiento se reinicia en cada sección H2."""

from nubbix_assist.chunking.contracts import Chunk
from nubbix_assist.chunking.factory import fingerprint, make_chunk
from nubbix_assist.chunking.sections import section_bodies
from nubbix_assist.ingestion.contracts import Document

from .words import word_windows


def chunk_by_section_words(document: Document, *, size: int = 80, overlap: int = 20) -> list[Chunk]:
    """Corta cada H2 de `document` en ventanas de hasta `size` palabras con `overlap` compartidas.

    Cada fragmento conserva el título del documento, el de su sección y los
    offsets de la evidencia sobre el Markdown original.
    """
    strategy = "section_words_v1"
    rule = fingerprint({"strategy": strategy, "size": size, "overlap": overlap,
                        "context": "title_sections_body_v1"})
    chunks = []
    for left, right, label in section_bodies(document):
        for start, end in word_windows(document.raw_text, left, right, size, overlap):
            chunks.append(make_chunk(document, strategy=strategy, strategy_fingerprint=rule,
                                     start_char=start, end_char=end, section_paths=(label,),
                                     ordinal=len(chunks) + 1))
    return chunks
