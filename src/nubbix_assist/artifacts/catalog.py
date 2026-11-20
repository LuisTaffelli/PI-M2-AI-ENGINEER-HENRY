import json
from dataclasses import asdict
from pathlib import Path

from nubbix_assist.chunking.contracts import Chunk


def write_catalog(path: Path, chunks: list[Chunk]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        for chunk in chunks:
            stream.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")


def read_catalog(path: Path) -> dict[str, Chunk]:
    catalog = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        data = json.loads(line)
        data["section_paths"] = tuple(data["section_paths"])
        chunk = Chunk(**data)
        if chunk.chunk_id in catalog:
            raise ValueError("El catálogo tiene IDs duplicados.")
        catalog[chunk.chunk_id] = chunk
    return catalog
