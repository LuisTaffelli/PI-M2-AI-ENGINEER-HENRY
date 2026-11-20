from urllib.parse import quote

from ...contracts.inputs import Request
from ...http import post_json
from .config import ENDPOINT
from .validators import parse_response


class GeminiProvider:
    name = "gemini"

    def __init__(self, model: str, key: str, timeout: int, output_tokens: int):
        self.model, self.key = model, key
        self.timeout, self.output_tokens = timeout, output_tokens

    def complete(self, request: Request):
        url = f"{ENDPOINT}/{quote(self.model, safe='')}:generateContent"
        payload = {"systemInstruction": {"parts": [{"text": request.system}]},
                   "contents": [{"role": "user", "parts": [{"text": request.user}]}],
                   "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": request.schema,
                                        "maxOutputTokens": self.output_tokens}}
        return parse_response(post_json(url, payload, {"x-goog-api-key": self.key}, self.timeout))
