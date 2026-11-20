from .index import BM25Index
from .tokenizer import tokenize


def search(index: BM25Index, question: str, limit: int, allowed: set[str]) -> list[tuple[str, float]]:
    terms = set(tokenize(question))
    scores = []
    for key in sorted(allowed):
        frequencies = index.frequencies[key]
        norm = index.k1 * (1 - index.b + index.b * index.lengths[key] / index.average_length)
        score = sum(index.idf[t] * frequencies[t] * (index.k1 + 1) / (frequencies[t] + norm)
                    for t in sorted(terms.intersection(frequencies)))
        if score > 0:
            scores.append((key, score))
    return sorted(scores, key=lambda item: (-item[1], item[0]))[:limit]
