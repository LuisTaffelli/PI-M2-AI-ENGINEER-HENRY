from ...contracts.inputs import Request
from ...http import post_json
from .config import ENDPOINT
from .validators import parse_response


class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str, key: str, timeout: int, output_tokens: int):
        self.model, self.key = model, key
        self.timeout, self.output_tokens = timeout, output_tokens

    def complete(self, request: Request):
        payload = {"model": self.model, "messages": [{"role": "system", "content": request.system},
                   {"role": "user", "content": request.user}], "max_completion_tokens": self.output_tokens,
                   "response_format": {"type": "json_schema", "json_schema": {
                       "name": request.schema_name, "strict": True, "schema": request.schema}}}
        return parse_response(post_json(ENDPOINT, payload, {"Authorization": f"Bearer {self.key}"}, self.timeout))
