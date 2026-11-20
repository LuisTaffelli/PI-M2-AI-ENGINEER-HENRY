import json
from dataclasses import asdict

from nubbix_assist.llm.contracts.inputs import Request
from .contracts.verdict import SCHEMA
from .validators import score_verdict


def judge(answer, model, prompt):
    completion = model.complete(Request(prompt, json.dumps(asdict(answer), ensure_ascii=False), SCHEMA, "groundedness"))
    payload = json.loads(completion.text)
    score = score_verdict(payload, {citation.chunk_id for citation in answer.chunks_related})
    return {"score": score, "claims": payload["claims"], "usage": completion.usage}
