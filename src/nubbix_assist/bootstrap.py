"""Ensamblado de las estrategias de inspección e ingesta."""

from functools import partial

from .chunking.strategies.headings import chunk_by_headings
from .chunking.strategies.words import chunk_by_words
from .ingestion.service import inspect_document

STRATEGIES = {"headings_v1": chunk_by_headings, "words_v1": chunk_by_words}
inspect_heading_document = partial(inspect_document, strategy=chunk_by_headings)


def local_embeddings(root):
    from .configuration.loader import load_config
    from .embeddings.providers.sentence_transformers.adapter import SentenceTransformerProvider, LocalModel
    from .embeddings.service import Embeddings

    config = LocalModel(**load_config(root)["embeddings"])
    return Embeddings(SentenceTransformerProvider(config))


def build(root, name):
    from .ingestion.build import build_index
    from .vector_store.providers.chroma.adapter import ChromaIndex

    return build_index(root, name, STRATEGIES[name], local_embeddings(root), ChromaIndex)


def load_build(root, build_id):
    from .artifacts.repository import open_build
    from .vector_store.providers.chroma.adapter import ChromaIndex

    return open_build(root, build_id, ChromaIndex)


def make_retriever(root, build_id, embeddings=None):
    from .configuration.loader import load_config
    from .retrieval.service import Retriever

    return Retriever(load_build(root, build_id), embeddings or local_embeddings(root), load_config(root)["retrieval"])


def language_model(root, role, budget):
    from dotenv import load_dotenv
    from .configuration.loader import load_config
    from .llm.providers import configured_provider
    from .llm.service import LanguageModel

    load_dotenv(root / ".env", override=False)
    config = load_config(root)["llm"]
    provider = configured_provider(role, config["timeout_seconds"], config["max_output_tokens"])
    return LanguageModel(provider, budget, config["max_input_bytes"])
