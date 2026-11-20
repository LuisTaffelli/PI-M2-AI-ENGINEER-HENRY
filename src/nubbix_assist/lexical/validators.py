from .index import BM25Index
from .tokenizer import TOKENIZER_VERSION


def validate(index: BM25Index, ids: set[str]) -> None:
    if index.tokenizer != TOKENIZER_VERSION or set(index.frequencies) != ids or set(index.lengths) != ids:
        raise ValueError("El estado BM25 no coincide con el catálogo o el tokenizador.")
