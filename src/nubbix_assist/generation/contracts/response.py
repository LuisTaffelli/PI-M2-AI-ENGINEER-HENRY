from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    source: str
    content: str
    score: float


@dataclass
class Answer:
    user_question: str
    system_answer: str
    chunks_related: list[Citation]


INSUFFICIENT = "La documentación disponible no alcanza para responder la pregunta."
SCHEMA = {"type": "object", "additionalProperties": False, "properties": {
    "system_answer": {"type": "string"}, "cited_chunk_ids": {"type": "array", "items": {"type": "string"}}},
    "required": ["system_answer", "cited_chunk_ids"]}
