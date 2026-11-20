from ...contracts.inputs import TextInput
from ...contracts.outputs import EmbeddedText
from ...contracts.provider import Role
from ...contracts.spec import EmbeddingSpec
from .config import LocalModel
from .validators import validate_lengths, validate_model


class SentenceTransformerProvider:
    def __init__(self, config: LocalModel):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(config.model, revision=config.revision,
                                         local_files_only=True, device="cpu")
        validate_model(config, self.model)
        self.spec = EmbeddingSpec("sentence_transformers", config.model, config.revision,
                                  config.dimension, config.max_tokens, True,
                                  config.query_prefix, config.document_prefix)

    def encode(self, inputs: list[TextInput], role: Role) -> list[EmbeddedText]:
        prefix = self.spec.query_prefix if role == "query" else self.spec.document_prefix
        texts = [prefix + item.text for item in inputs]
        validate_lengths(self.model.tokenizer, texts, self.spec.max_tokens)
        vectors = self.model.encode(texts, normalize_embeddings=True, prompt="", show_progress_bar=False)
        return [EmbeddedText(item.id, vector.tolist()) for item, vector in zip(inputs, vectors, strict=True)]
