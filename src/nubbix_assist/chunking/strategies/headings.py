"""Un chunk por sección H2 del corpus, con offsets sobre el texto original."""

import re
from collections.abc import Iterator

from nubbix_assist.chunking.contracts import Chunk
from nubbix_assist.chunking.factory import fingerprint, make_chunk
from nubbix_assist.ingestion.contracts import Document


STRATEGY = "headings_v1"
STRATEGY_FINGERPRINT = fingerprint({"strategy": STRATEGY, "context": "title_sections_body_v1"})

_HEADING = re.compile(r" {0,3}##(?:[ \t]+(.*)|$)")
_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")


def _section_headings(document: Document) -> Iterator[tuple[int, int, str]]:
    offset = 0
    fence = ""
    for line in document.raw_text.splitlines(keepends=True):
        start = offset
        offset += len(line)
        text = line.rstrip("\r\n")
        marker = _FENCE.fullmatch(text)
        if marker:
            delimiter, info = marker.groups()
            if fence:
                if delimiter.startswith(fence) and not info.strip():
                    fence = ""
            elif delimiter[0] == "~" or "`" not in info:
                fence = delimiter
            continue
        if not fence and (heading := _HEADING.fullmatch(text)):
            label = re.sub(r"(?:^|[ \t]+)#+[ \t]*$", "", heading[1] or "").strip()
            if not label:
                raise ValueError(f"{document.source}: encabezado H2 sin nombre en {start}.")
            yield start, offset, label


def chunk_by_headings(document: Document) -> list[Chunk]:
    headings = list(_section_headings(document))
    if not headings:
        raise ValueError(f"{document.source}: no se encontraron secciones H2.")

    chunks = []
    for index, (_, body_start, label) in enumerate(headings):
        following = index + 1
        body_end = headings[following][0] if following < len(headings) else len(document.raw_text)
        chunks.append(make_chunk(
            document, strategy=STRATEGY, strategy_fingerprint=STRATEGY_FINGERPRINT,
            start_char=body_start, end_char=body_end, section_paths=(label,), ordinal=following,
        ))
    return chunks
