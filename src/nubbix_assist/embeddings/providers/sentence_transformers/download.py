"""Descarga explícita del snapshot que después abrirá el adaptador en modo local."""

from .config import LocalModel


def download_model(config: LocalModel) -> str:
    from huggingface_hub import snapshot_download

    return snapshot_download(
        config.model, revision=config.revision,
        allow_patterns=["*.json", "model.safetensors", "sentencepiece.bpe.model"],
        ignore_patterns=["onnx/*", "openvino/*", ".eval_results/*"])
