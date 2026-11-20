from dataclasses import asdict
import json
from pathlib import Path
from uuid import uuid4

from nubbix_assist.artifacts.validators import digest
from nubbix_assist.generation.service import generate
from .contracts.result import QueryResult


def answer_retrieval(root: Path, retrieval, model, prompt: str) -> QueryResult:
    run_id = uuid4().hex
    directory = root / "runs" / run_id
    directory.mkdir(parents=True)
    trace = {"run_id": run_id, "retrieval": asdict(retrieval), "prompt_sha256": digest(prompt), "attempts": []}
    try:
        answer = generate(retrieval, model, prompt, trace["attempts"])
        trace["answer"] = asdict(answer)
        return QueryResult(run_id, answer, retrieval)
    except (ValueError, RuntimeError) as error:
        trace["error"] = str(error)
        raise
    finally:
        (directory / "query.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
