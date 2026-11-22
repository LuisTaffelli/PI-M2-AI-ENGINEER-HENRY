"""Cross-encoder multilingüe local para puntuar pares de pregunta y fragmento."""
from math import isfinite

MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
REVISION = "1427fd652930e4ba29e8149678df786c240d8825"
FILES = ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
         "special_tokens_map.json", "sentencepiece.bpe.model"]


def prepare_reranker():
    from huggingface_hub import snapshot_download
    return snapshot_download(MODEL, revision=REVISION, allow_patterns=FILES, token=False)


class LocalReranker:
    model_id = MODEL
    revision = REVISION

    def __init__(self):
        from sentence_transformers import CrossEncoder
        try:
            self.model = CrossEncoder(MODEL, revision=REVISION, local_files_only=True, device="cpu")
        except OSError as exc:
            raise ValueError("Prepará el cross-encoder con python ingest/run.py prepare-reranker.") from exc

    def score(self, question, chunks):
        pairs = [(question, chunk.content) for chunk in chunks]
        scores = self.model.predict(pairs, batch_size=10, show_progress_bar=False)
        if not all(isfinite(score) for score in scores):
            raise ValueError("El cross-encoder devolvió un puntaje no finito.")
        return [float(score) for score in scores]
