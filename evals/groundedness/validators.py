def score_verdict(data, allowed):
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise ValueError("El juez devolvió un veredicto inválido.")
    claims = data["claims"]
    for claim in claims:
        if (not isinstance(claim, dict) or claim.get("status") not in ("supported", "unsupported", "uncertain")
                or not isinstance(claim.get("claim"), str) or not claim["claim"].strip()
                or not isinstance(claim.get("reason"), str) or not claim["reason"].strip()
                or not isinstance(claim.get("ids"), list) or any(not isinstance(i, str) for i in claim["ids"])
                or not set(claim["ids"]) <= allowed or (claim["status"] == "supported" and not claim["ids"])):
            raise ValueError("El juez devolvió una afirmación o referencia inválida.")
    return sum(c["status"] == "supported" for c in claims) / len(claims) if claims else None
