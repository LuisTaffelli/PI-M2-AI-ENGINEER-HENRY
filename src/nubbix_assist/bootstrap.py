"""Ensamblado de las estrategias de inspección e ingesta."""

from functools import partial

from .chunking.strategies.headings import chunk_by_headings
from .chunking.strategies.section_words import chunk_by_section_words
from .chunking.strategies.words import chunk_by_words
from .ingestion.service import inspect_document

STRATEGIES = {"headings_v1": chunk_by_headings, "words_v1": chunk_by_words,
              "section_words_v1": chunk_by_section_words}
inspect_heading_document = partial(inspect_document, strategy=chunk_by_headings)


def local_embeddings(root):
    from .configuration.loader import load_config
    from .embeddings.providers.sentence_transformers.adapter import SentenceTransformerProvider, LocalModel
    from .embeddings.service import Embeddings

    config = LocalModel(**load_config(root)["embeddings"])
    return Embeddings(SentenceTransformerProvider(config))


def prepare_local_model(root):
    from .configuration.loader import load_config
    from .embeddings.providers.sentence_transformers.config import LocalModel
    from .embeddings.providers.sentence_transformers.download import download_model

    return download_model(LocalModel(**load_config(root)["embeddings"]))


def build(root, name, *, timings=None):
    from .ingestion.build import build_index
    from .vector_store.providers.chroma.adapter import ChromaIndex

    from .timing import measure

    timings = {} if timings is None else timings
    with measure(timings, "ingestion_total"):
        with measure(timings, "embedding_model_load"):
            embeddings = local_embeddings(root)
        return build_index(root, name, STRATEGIES[name], embeddings, ChromaIndex, timings=timings)


def load_build(root, build_id):
    from .artifacts.repository import open_build
    from .vector_store.providers.chroma.adapter import ChromaIndex

    return open_build(root, build_id, ChromaIndex)


def make_retriever(root, build_id, embeddings=None, *, rerank=False, multi_query=False):
    from .configuration.loader import load_config
    from .retrieval.service import Retriever
    from .retrieval.rerank import LocalReranker

    return Retriever(load_build(root, build_id), embeddings or local_embeddings(root), load_config(root)["retrieval"],
                     reranker=LocalReranker() if rerank else None, multi_query=multi_query)


def language_model(root, role, budget):
    from dotenv import load_dotenv
    from .configuration.loader import load_config
    from .llm.providers import configured_provider
    from .llm.service import LanguageModel

    load_dotenv(root / ".env", override=False)
    config = load_config(root)["llm"]
    provider = configured_provider(role, config["timeout_seconds"], config["max_output_tokens"])
    return LanguageModel(provider, budget, config["max_input_bytes"])
