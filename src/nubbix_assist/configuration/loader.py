from pathlib import Path


def load_config(root: Path) -> dict:
    import yaml

    config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    retrieval = config["retrieval"]
    if not 0 < retrieval["top_k"] <= retrieval["candidates"] or retrieval["rrf_constant"] <= 0:
        raise ValueError("Parámetros de recuperación inválidos.")
    return config
