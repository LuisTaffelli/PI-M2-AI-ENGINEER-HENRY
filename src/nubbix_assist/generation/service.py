import json

from nubbix_assist.llm.contracts.inputs import Request
from nubbix_assist.llm.errors import ProviderError
from nubbix_assist.timing import measure
from .citations import resolve
from .context import context_items
from .contracts.response import Answer, SCHEMA
from .validators import validate_answer


def generate(retrieval, model, prompt: str, attempts: list) -> Answer:
    context = context_items(retrieval.selected)
    evidence = {"pregunta": retrieval.question, "contexto": context}
    for attempt in range(1, 3):
        record = {"attempt": attempt, "provider": model.provider.name, "model": model.provider.model}
        attempts.append(record)
        try:
            with measure(record, "model_ms"):
                completion = model.complete(Request(prompt, json.dumps(evidence, ensure_ascii=False), SCHEMA, "answer"))
            record.update(usage=completion.usage, finish=completion.finish)
            answer, ids = validate_answer(json.loads(completion.text), {row["chunk_id"] for row in context})
            return Answer(retrieval.question, answer, resolve(ids, retrieval.selected))
        except (ProviderError, ValueError) as error:
            record["error"] = str(error)
            if attempt == 2 or (isinstance(error, ProviderError) and not error.retryable):
                raise
            evidence["correccion"] = "Revisá el formato y las citas. " + str(error)
    raise RuntimeError("Se agotaron los intentos de generación.")
