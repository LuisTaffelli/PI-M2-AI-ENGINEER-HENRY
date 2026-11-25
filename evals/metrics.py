from math import ceil
from statistics import mean, median


def retrieval_metrics(retrieved, expected, k):
    if not expected:
        return None
    expected = set(expected)
    top = retrieved[:k]
    hits = len(set(top).intersection(expected))
    rr = next((1 / rank for rank, chunk in enumerate(top, 1) if chunk in expected), 0.0)
    return {"precision_at_k": hits / k, "recall_at_k": hits / len(expected),
            "hit": int(hits > 0), "rr_at_k": rr}


def retrieval_macro(valid):
    if not valid:
        return {}
    return {**{key: mean(r[key] for r in valid) for key in ("precision_at_k", "recall_at_k", "hit")},
            "mrr_at_k": mean(r["rr_at_k"] for r in valid)}


def latency_summary(samples):
    groups = {}
    for row in samples:
        for stage, elapsed in row.items():
            groups.setdefault(stage, []).append(elapsed)
    return {stage: {"n": len(times), "median_ms": median(times),
                    "p95_ms": sorted(times)[ceil(.95 * len(times)) - 1]}
            for stage, times in groups.items()}


def summarize(rows):
    valid = [r["retrieval"] for r in rows if r.get("retrieval") is not None]
    scores = [r["judge"]["score"] for r in rows if r.get("judge", {}).get("score") is not None]
    refusals = [r["correct_refusal"] for r in rows if "correct_refusal" in r]
    out_of_scope = [r for r in rows if r.get("answerable") is False]
    ranking = {}
    for row in rows:
        for mode, cuts in row.get("rankings", {}).items():
            for k, metrics in cuts.items():
                if metrics is not None:
                    ranking.setdefault(mode, {}).setdefault(k, []).append(metrics)
    return {
        "total": len(rows), "retrieval_scored": len(valid),
        "retrieval_errors": sum("retrieval_error" in r for r in rows),
        "retrieval_macro": retrieval_macro(valid),
        "rankings_macro": {mode: {k: dict(retrieval_macro(samples), n=len(samples))
                                  for k, samples in cuts.items()} for mode, cuts in ranking.items()},
        "timings_ms": latency_summary(r.get("timing_ms", {}) for r in rows),
        "generation_completed": sum("answer" in r for r in rows),
        "generation_errors": sum("generation_error" in r for r in rows),
        "judge_errors": sum("judge_error" in r for r in rows),
        "groundedness_scored": len(scores),
        "groundedness_not_applicable": sum(r.get("judge", {}).get("score", -1) is None for r in rows),
        "groundedness_macro": mean(scores) if scores else None,
        "out_of_scope_expected": len(out_of_scope), "out_of_scope_answered": len(refusals),
        "out_of_scope_correct": sum(refusals) if refusals else None,
        "out_of_scope_errors": sum(bool({"retrieval_error", "generation_error"} & r.keys()) for r in out_of_scope),
        "out_of_scope_not_run": sum("correct_refusal" not in r and
                                    not ({"retrieval_error", "generation_error"} & r.keys()) for r in out_of_scope),
        "correct_refusal_rate": mean(refusals) if refusals else None,
    }
