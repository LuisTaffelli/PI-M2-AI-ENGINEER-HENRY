import re

from ...errors import EmbeddingError


def validate_model(config, model) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", config.revision):
        raise EmbeddingError("La revisión debe identificar un commit exacto del modelo.")
    if model.get_sentence_embedding_dimension() != config.dimension or model.max_seq_length < config.max_tokens:
        raise EmbeddingError("La dimensión o el límite real del modelo difiere de la configuración.")


def validate_lengths(tokenizer, texts: list[str], limit: int) -> None:
    ids = tokenizer(texts, truncation=False, padding=False)["input_ids"]
    if any(len(tokens) > limit for tokens in ids):
        raise EmbeddingError(f"El texto preparado supera el límite de {limit} tokens.")
