"""Reformulación determinista del registro de chat al vocabulario documental."""
from difflib import get_close_matches
import re
import unicodedata


# Vocabulario de uso laboral. Solo traduce términos; las políticas viven en los documentos.
_ALIASES = {
    "q": "qué", "x": "por", "dps": "después", "dsd": "desde", "tpo": "tiempo",
    "1ra": "primera", "flia": "familia", "laburo": "trabajo", "laburando": "trabajando",
    "compu": "equipo de cómputo", "computadora": "equipo de cómputo", "notebook": "equipo de cómputo",
    "notebooks": "equipos de cómputo", "laptop": "equipo de cómputo", "vacas": "vacaciones",
    "parcial": "examen", "prod": "producción", "bd": "base de datos", "pass": "contraseña",
    "wifi": "Wi-Fi", "soft": "software", "tecno": "tecnología", "ok": "aprobación",
}
_WORD = re.compile(r"(?<![\w#@./-])\w+(?![\w./-])", re.UNICODE)
_SPLIT = re.compile(r"(?:[?;]\s*(?:y\s+)?|[,\s]+y\s+)(?=¿?(?:qué|que|cómo|como|cuán\w*|cuan\w*|quién|quien|dónde|donde|hasta)\b)", re.I)


def _plain(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold()) if not unicodedata.combining(c))


class QueryRewriter:
    def __init__(self, vocabulary):
        self.terms = {_plain(term): term for term in sorted(vocabulary) if term.isalpha()}

    def variants(self, question):
        def replace(match):
            word = match.group()
            key = _plain(word)
            if key in _ALIASES:
                return _ALIASES[key]
            if not word.isalpha() or word.isupper():
                return word
            if key in self.terms:
                return self.terms[key]
            if 5 <= len(key) <= 32:
                for i in range(len(key) - 1):
                    swapped = key[:i] + key[i:i+2][::-1] + key[i+2:]
                    if swapped in self.terms:
                        return self.terms[swapped]
            if 6 <= len(key) <= 32:
                near = get_close_matches(key, self.terms, n=1, cutoff=0.88)
                if near:
                    return self.terms[near[0]]
            return word

        normalized = _WORD.sub(replace, question)
        parts = _SPLIT.split(normalized.strip("¿? "), maxsplit=1)
        candidates = [normalized]
        if len(parts) == 2 and all(len(part.split()) >= 3 for part in parts):
            candidates.extend(part.strip(" ¿?,") for part in parts)
        seen = {" ".join(question.casefold().split())}
        variants = []
        for item in candidates:
            key = " ".join(item.casefold().split())
            if key and key not in seen:
                seen.add(key)
                variants.append(item)
        return variants
