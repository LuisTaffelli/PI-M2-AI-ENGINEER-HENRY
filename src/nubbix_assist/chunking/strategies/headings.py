"""Un chunk por sección H2 del corpus, con offsets sobre el texto original."""

from nubbix_assist.chunking.sections import section_bodies

from nubbix_assist.chunking.contracts import Chunk
from nubbix_assist.chunking.factory import fingerprint, make_chunk
from nubbix_assist.ingestion.contracts import Document


STRATEGY = "headings_v1"
STRATEGY_FINGERPRINT = fingerprint({"strategy": STRATEGY, "context": "title_sections_body_v1"})

def chunk_by_headings(document: Document) -> list[Chunk]:
    chunks = []
    for ordinal, (body_start, body_end, label) in enumerate(section_bodies(document), start=1):
        chunks.append(make_chunk(
            document, strategy=STRATEGY, strategy_fingerprint=STRATEGY_FINGERPRINT,
            start_char=body_start, end_char=body_end, section_paths=(label,), ordinal=ordinal,
        ))
    return chunks
