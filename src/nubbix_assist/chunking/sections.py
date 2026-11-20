"""Límites de secciones Markdown compartidos por las estrategias."""

import re
from collections.abc import Iterator

from nubbix_assist.ingestion.contracts import Document


_HEADING = re.compile(r" {0,3}##(?:[ \t]+(.*)|$)")
_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")


def section_headings(document: Document) -> Iterator[tuple[int, int, str]]:
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
