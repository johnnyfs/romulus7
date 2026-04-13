from collections.abc import Iterable
from typing import Any

from fastapi import Request
from sqlmodel import SQLModel


class Filters:
    KNOWN_OPERATORS = {"in"}

    def __init__(self, filters: list[tuple[str, str, Any]]):
        self.filters = filters

    @classmethod
    async def from_request(cls, request: Request):
        filters = []
        for key, value in request.query_params.multi_items():
            for op in cls.KNOWN_OPERATORS:
                if key.endswith(f".{op}"):
                    filters.append((key[: -(len(op) + 1)], op, value))
        return cls(filters)

    def apply(self, stmt, model: type[SQLModel]):
        for field, op, value in self.filters:
            if op == "in":
                stmt = stmt.where(self._resolve_field(model, field).in_(self._split_csv(value)))
        return stmt

    def _resolve_field(self, model: type[SQLModel], field: str):
        parts = field.split(".")
        expr = getattr(model, parts[0])
        for part in parts[1:]:
            expr = expr[part]
        if len(parts) > 1 and hasattr(expr, "as_string"):
            expr = expr.as_string()
        return expr

    def _split_csv(self, value: Any) -> list[str]:
        if isinstance(value, str):
            return [item for item in value.split(",") if item]
        if isinstance(value, Iterable):
            return [str(item) for item in value]
        return [str(value)]
