import json

from .contracts.inputs import Request
from .errors import ProviderError


def validate_request(request: Request, byte_limit: int) -> None:
    size = sum(len(s.encode("utf-8")) for s in (request.system, request.user, json.dumps(request.schema)))
    if size > byte_limit:
        raise ProviderError("El contexto supera el presupuesto de entrada configurado.")
