from dataclasses import dataclass

from .contracts.inputs import Request
from .contracts.provider import Provider
from .errors import ProviderError
from .validators import validate_request


@dataclass
class CallBudget:
    limit: int
    used: int = 0

    def consume(self):
        if self.used >= self.limit:
            raise ProviderError("Se agotó el presupuesto de llamadas de la corrida.")
        self.used += 1


class LanguageModel:
    def __init__(self, provider: Provider, budget: CallBudget, max_input_bytes: int):
        self.provider = provider
        self.budget = budget
        self.max_input_bytes = max_input_bytes

    def complete(self, request: Request):
        validate_request(request, self.max_input_bytes)
        self.budget.consume()
        return self.provider.complete(request)
