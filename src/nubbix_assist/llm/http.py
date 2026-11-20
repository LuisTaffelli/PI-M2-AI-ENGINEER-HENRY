"""Transporte JSON de un solo intento. Las credenciales viajan en los encabezados."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import ProviderError


def post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    request = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        raise ProviderError(f"La API devolvió HTTP {error.code}.",
                            retryable=error.code in {408, 429} or error.code >= 500) from error
    except (URLError, TimeoutError, ConnectionError) as error:
        raise ProviderError("Falló la conexión con la API.", retryable=True) from error
    except (ValueError, UnicodeError) as error:
        raise ProviderError("La API devolvió una respuesta ilegible.", retryable=True) from error
