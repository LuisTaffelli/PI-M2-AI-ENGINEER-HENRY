from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    system: str
    user: str
    schema: dict
    schema_name: str
