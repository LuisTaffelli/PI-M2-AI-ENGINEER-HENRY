"""Carga los Markdown del corpus conservando el contenido y los saltos de línea."""

from hashlib import sha256
from pathlib import Path
import re

from .contracts import Document
from .revisions import revision_source


def load_markdown(source: Path, *, project_root: Path, version: str | None = None) -> Document:
    root = project_root.resolve()
    relative = (root / source).resolve().relative_to(root)
    path, label, expected = revision_source(root, relative, version)
    document = parse_markdown(relative, path.read_bytes(), label)
    if expected is not None and document.source_sha256 != expected:
        raise ValueError(f"{relative}: el contenido registrado como «{label}» cambió en disco.")
    return document


def parse_markdown(source: Path, raw_bytes: bytes, version: str) -> Document:
    relative_path = source.as_posix()
    text = raw_bytes.decode("utf-8")
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    heading = re.fullmatch(r" {0,3}#[ \t]+(.+)", first_line.removeprefix("\ufeff"))
    title = re.sub(r"[ \t]+#+[ \t]*$", "", heading[1]).strip() if heading else ""
    if not title:
        raise ValueError(f"{relative_path}: se esperaba un título H1 al inicio del documento.")
    return Document(
        source=relative_path,
        title=title,
        source_sha256=sha256(raw_bytes).hexdigest(),
        raw_text=text,
        version=version,
    )
