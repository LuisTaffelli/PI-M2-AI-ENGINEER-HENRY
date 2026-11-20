from pathlib import Path


def load_prompt(root: Path, name: str) -> str:
    import yaml

    prompt = yaml.safe_load((root / "prompts" / f"{name}.yaml").read_text(encoding="utf-8"))
    return prompt["system"]
