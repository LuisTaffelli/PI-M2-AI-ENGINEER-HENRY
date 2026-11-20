from collections import Counter
from dataclasses import dataclass
from math import log1p

from nubbix_assist.chunking.contracts import Chunk
from .tokenizer import TOKENIZER_VERSION, tokenize


@dataclass
class BM25Index:
    frequencies: dict[str, dict[str, int]]
    lengths: dict[str, int]
    idf: dict[str, float]
    average_length: float
    k1: float = 1.2
    b: float = 0.75
    tokenizer: str = TOKENIZER_VERSION

    @classmethod
    def build(cls, chunks: list[Chunk]):
        frequencies = {c.chunk_id: dict(Counter(tokenize(c.content))) for c in chunks}
        lengths = {key: sum(counts.values()) for key, counts in frequencies.items()}
        documents = Counter(term for counts in frequencies.values() for term in counts)
        size = len(chunks)
        if not size or not sum(lengths.values()):
            raise ValueError("El índice léxico requiere contenido.")
        idf = {term: log1p((size - count + 0.5) / (count + 0.5)) for term, count in documents.items()}
        return cls(frequencies, lengths, idf, sum(lengths.values()) / size)
