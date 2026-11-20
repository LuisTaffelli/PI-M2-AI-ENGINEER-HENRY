from ...contracts.outputs import Completion
from ...errors import ProviderError


def parse_response(result: dict) -> Completion:
    try:
        choice = result["choices"][0]
        text = choice["message"]["content"]
        if choice["finish_reason"] != "stop" or not isinstance(text, str):
            raise ValueError
        return Completion(text, result.get("usage", {}), choice["finish_reason"])
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise ProviderError("OpenAI no devolvió una respuesta completa.", retryable=True) from error
