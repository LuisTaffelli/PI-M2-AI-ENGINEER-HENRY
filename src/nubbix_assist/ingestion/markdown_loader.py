"""Carga los Markdown del corpus conservando el contenido y los saltos de línea."""

from hashlib import sha256
from pathlib import Path
import re

from .contracts import Document


def load_markdown(source: Path, *, project_root: Path) -> Document:
    root = project_root.resolve()
    path = (root / source).resolve()
    relative_path = path.relative_to(root).as_posix()
    raw_bytes = path.read_bytes()
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
    )
