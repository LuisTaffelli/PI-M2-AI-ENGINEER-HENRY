from dataclasses import dataclass
from nubbix_assist.generation.contracts.response import Answer
from nubbix_assist.retrieval.contracts.candidates import Retrieval


@dataclass
class QueryResult:
    run_id: str
    answer: Answer
    retrieval: Retrieval
