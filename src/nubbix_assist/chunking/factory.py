"""Construcción del texto preparado y de la identidad compartida por las estrategias."""

import json
from hashlib import sha256

from nubbix_assist.ingestion.contracts import Document

from .contracts import Chunk


def fingerprint(fields: dict[str, str | int]) -> str:
    encoded = json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def make_chunk(
    document: Document,
    *,
    strategy: str,
    strategy_fingerprint: str,
    start_char: int,
    end_char: int,
    section_paths: tuple[str, ...],
    ordinal: int,
) -> Chunk:
    body = document.raw_text[start_char:end_char]
    context = "\n".join((document.title, *section_paths))
    content = f"{context}\n\n{body}"
    content_sha256 = sha256(content.encode("utf-8")).hexdigest()
    identity_fields = {
        "schema_version": 1,
        "source": document.source,
        "source_sha256": document.source_sha256,
        "strategy": strategy,
        "strategy_fingerprint": strategy_fingerprint,
        "start_char": start_char,
        "end_char": end_char,
        "content_sha256": content_sha256,
    }
    # Los IDs de la edición original ya están citados en el golden y en respuestas guardadas.
    if document.version != "1":
        identity_fields["version"] = document.version
    return Chunk(
        chunk_id=fingerprint(identity_fields),
        source=document.source,
        source_sha256=document.source_sha256,
        strategy=strategy,
        strategy_fingerprint=strategy_fingerprint,
        start_char=start_char,
        end_char=end_char,
        section_paths=section_paths,
        body=body,
        content=content,
        content_sha256=content_sha256,
        ordinal=ordinal,
        version=document.version,
    )
