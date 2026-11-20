"""Ensamblado de las estrategias de inspección e ingesta."""

from functools import partial

from .chunking.strategies.headings import chunk_by_headings
from .chunking.strategies.words import chunk_by_words
from .ingestion.service import inspect_document

STRATEGIES = {"headings_v1": chunk_by_headings, "words_v1": chunk_by_words}
inspect_heading_document = partial(inspect_document, strategy=chunk_by_headings)
