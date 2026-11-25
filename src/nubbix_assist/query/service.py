from dataclasses import asdict
import json
from pathlib import Path
from uuid import uuid4

from nubbix_assist.artifacts.validators import digest
from nubbix_assist.generation.service import generate
from .contracts.result import QueryResult
from nubbix_assist.timing import measure


def answer_retrieval(root: Path, retrieval, model, prompt: str) -> QueryResult:
    """Genera una respuesta con `model` y `prompt` a partir de la evidencia de `retrieval`.

    Guarda la traza en `runs/` bajo `root` y devuelve el ID de corrida, la respuesta
    con sus citas y la recuperación que se usó para generarla.
    """
    run_id = uuid4().hex
    directory = root / "runs" / run_id
    directory.mkdir(parents=True)
    trace = {"run_id": run_id, "retrieval": asdict(retrieval), "prompt_sha256": digest(prompt), "attempts": []}
    durations = trace["timing_ms"] = {"retrieval_total": retrieval.elapsed_ms}
    try:
        with measure(durations, "generation"):
            answer = generate(retrieval, model, prompt, trace["attempts"])
        trace["answer"] = asdict(answer)
        return QueryResult(run_id, answer, retrieval)
    except (ValueError, RuntimeError) as error:
        trace["error"] = str(error)
        raise
    finally:
        durations["query_total"] = durations["retrieval_total"] + durations.get("generation", 0)
        (directory / "query.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
