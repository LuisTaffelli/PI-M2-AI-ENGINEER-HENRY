"""Ensamblado de los casos de uso disponibles en la aplicación."""

from functools import partial

from .chunking.strategies.headings import chunk_by_headings
from .ingestion.service import inspect_document

inspect_heading_document = partial(inspect_document, strategy=chunk_by_headings)
