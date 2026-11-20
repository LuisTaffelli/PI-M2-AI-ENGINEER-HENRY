import re
from .contracts.response import INSUFFICIENT


def validate_answer(payload: dict, allowed: set[str]) -> tuple[str, list[str]]:
    if not isinstance(payload, dict) or set(payload) != {"system_answer", "cited_chunk_ids"}:
        raise ValueError("Formato de respuesta inválido.")
    answer, ids = payload["system_answer"], payload["cited_chunk_ids"]
    if (not isinstance(answer, str) or not answer.strip() or not isinstance(ids, list)
            or any(not isinstance(key, str) for key in ids)):
        raise ValueError("Texto o referencias inválidas.")
    referenced = re.findall(r"\[([^\[\]]+)\]", answer)
    if set(referenced) != set(ids) or len(ids) != len(set(ids)) or not set(ids) <= allowed:
        raise ValueError("Las citas deben coincidir con el texto y pertenecer al contexto.")
    if (answer == INSUFFICIENT) != (not ids):
        raise ValueError("Una respuesta factual requiere citas.")
    return answer, ids
