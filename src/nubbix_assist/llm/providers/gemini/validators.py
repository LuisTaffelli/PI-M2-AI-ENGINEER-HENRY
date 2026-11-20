from ...contracts.outputs import Completion
from ...errors import ProviderError


def parse_response(result: dict) -> Completion:
    try:
        candidate = result["candidates"][0]
        if candidate["finishReason"] != "STOP":
            raise ValueError
        text = "".join(part["text"] for part in candidate["content"]["parts"] if not part.get("thought"))
        if not text:
            raise ValueError
        return Completion(text, result.get("usageMetadata", {}), "STOP")
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise ProviderError("Gemini no devolvió una respuesta completa.", retryable=True) from error
