"""Registro de adaptadores. La generación y el juez eligen proveedor por separado."""

import os

from .gemini.adapter import GeminiProvider
from .gemini.config import KEY_VARIABLE as GEMINI_KEY
from .openai.adapter import OpenAIProvider
from .openai.config import KEY_VARIABLE as OPENAI_KEY

PROVIDERS = {"openai": (OpenAIProvider, OPENAI_KEY), "gemini": (GeminiProvider, GEMINI_KEY)}


def configured_provider(role: str, timeout: int, output_tokens: int):
    provider = os.environ.get(f"NUBBIX_{role}_PROVIDER", "").lower()
    model = os.environ.get(f"NUBBIX_{role}_MODEL", "").strip()
    if provider not in PROVIDERS or not model:
        raise ValueError(f"Definí NUBBIX_{role}_PROVIDER (openai/gemini) y NUBBIX_{role}_MODEL.")
    adapter, variable = PROVIDERS[provider]
    key = os.environ.get(variable)
    if not key:
        raise ValueError(f"Falta {variable} para el proveedor {provider}.")
    return adapter(model, key, timeout, output_tokens)
