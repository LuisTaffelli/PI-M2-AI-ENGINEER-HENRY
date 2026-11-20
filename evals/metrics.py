from statistics import mean


def retrieval_metrics(retrieved, expected, k):
    if not expected:
        return None
    hits = len(set(retrieved[:k]).intersection(expected))
    return {"precision_at_k": hits / k, "recall_at_k": hits / len(set(expected)), "hit": int(hits > 0)}


def summarize(rows):
    valid = [r["retrieval"] for r in rows if r.get("retrieval") is not None]
    scores = [r["judge"]["score"] for r in rows if r.get("judge", {}).get("score") is not None]
    refusals = [r["correct_refusal"] for r in rows if "correct_refusal" in r]
    return {
        "total": len(rows), "retrieval_scored": len(valid),
        "retrieval_errors": sum("retrieval_error" in r for r in rows),
        "retrieval_macro": {key: mean(r[key] for r in valid) for key in ("precision_at_k", "recall_at_k", "hit")} if valid else {},
        "generation_completed": sum("answer" in r for r in rows),
        "generation_errors": sum("generation_error" in r for r in rows),
        "judge_errors": sum("judge_error" in r for r in rows),
        "groundedness_scored": len(scores),
        "groundedness_not_applicable": sum(r.get("judge", {}).get("score", -1) is None for r in rows),
        "groundedness_macro": mean(scores) if scores else None,
        "out_of_scope_answered": len(refusals), "correct_refusal_rate": mean(refusals) if refusals else None,
    }
