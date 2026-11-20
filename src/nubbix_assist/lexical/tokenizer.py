"""Tokens de BM25. Conserva códigos, canales, acentos y montos."""

import re

TOKENIZER_VERSION = "unicode_codes_v1"
_PATTERN = re.compile(r"#?\w+(?:[-.,]\w+)*", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _PATTERN.findall(text.casefold())
