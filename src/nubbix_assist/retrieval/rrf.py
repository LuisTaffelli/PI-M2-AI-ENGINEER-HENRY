def fuse(rankings: list[list[str]], constant: int, limit: int) -> list[tuple[str, float]]:
    scores = {}
    for ranking in rankings:
        for rank, key in enumerate(dict.fromkeys(ranking), start=1):
            scores[key] = scores.get(key, 0.0) + 1 / (constant + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
