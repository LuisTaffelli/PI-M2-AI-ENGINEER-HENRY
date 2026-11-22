"""Revisiones editoriales de los Markdown originales del corpus."""
import errno
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory


def _history(directory: Path):
    # El orden de registro es independiente de la etiqueta elegida por el editor.
    entries = sorted((p for p in directory.glob("[0-9]*") if p.name.isdecimal()),
                     key=lambda p: int(p.name))
    for entry in entries:
        yield entry, json.loads((entry / "metadata.json").read_text(encoding="utf-8"))


def revision_source(root: Path, source: Path, version: str | None) -> tuple[Path, str, str | None]:
    if version != "1" and source.parent == Path("data/corpus"):
        chosen = None
        for entry, metadata in _history(root / "data/revisions" / source.stem):
            if version is None or metadata["version"] == version:
                chosen = entry / "document.md", metadata["version"], metadata["sha256"]
        if chosen:
            return chosen
    if version not in (None, "1"):
        raise ValueError(f"{source}: versión desconocida «{version}».")
    return root / source, "1", None


def register_version(root: Path, source: Path, edited: Path, version: str) -> Path:
    from .markdown_loader import parse_markdown
    from nubbix_assist.chunking.strategies.headings import chunk_by_headings
    from nubbix_assist.chunking.validators import validate_chunks

    source = (root / source).resolve().relative_to(root.resolve())
    originals = json.loads((root / "docs/fuentes/procedencia.json").read_text())["corpus"]["files"]
    expected = next((item["sha256"] for item in originals if item["path"] == source.as_posix()), None)
    if expected is None or source.parent != Path("data/corpus"):
        raise ValueError(f"{source}: elegí un documento del corpus.")
    if sha256((root / source).read_bytes()).hexdigest() != expected:
        raise ValueError(f"Guardá una copia de tus cambios, restaurá {source} y pasá la copia con --file.")
    if not version.strip() or version != version.strip() or not version.isprintable() or version == "1":
        raise ValueError("Elegí una etiqueta nueva, sin espacios en los extremos. «1» identifica el original.")
    raw = edited.read_bytes()
    document = parse_markdown(source, raw, version)
    validate_chunks(document, chunk_by_headings(document))
    directory = root / "data/revisions" / source.stem
    directory.mkdir(parents=True, exist_ok=True)
    metadata = {"version": version, "sha256": document.source_sha256}
    with TemporaryDirectory(dir=directory, prefix=".registro-") as temp:
        staged = Path(temp) / "revision"
        staged.mkdir()
        (staged / "document.md").write_bytes(raw)
        (staged / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")
        while True:
            sequence = 0
            for entry, previous in _history(directory):
                sequence = int(entry.name)
                if previous["version"] == version:
                    if previous == metadata and (entry / "document.md").read_bytes() == raw:
                        return entry
                    raise ValueError(f"{source}: la versión «{version}» ya identifica otro contenido.")
            destination = directory / str(sequence + 1)
            try:
                staged.rename(destination)
                return destination
            except OSError as error:
                # Otra publicación pudo ocupar el mismo número mientras se preparaba la copia.
                if error.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                    raise
