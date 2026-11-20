ITEM = {"type": "object", "additionalProperties": False, "properties": {
    "claim": {"type": "string"}, "status": {"type": "string", "enum": ["supported", "unsupported", "uncertain"]},
    "reason": {"type": "string"}, "ids": {"type": "array", "items": {"type": "string"}}},
    "required": ["claim", "status", "reason", "ids"]}
SCHEMA = {"type": "object", "additionalProperties": False,
          "properties": {"claims": {"type": "array", "items": ITEM}}, "required": ["claims"]}
