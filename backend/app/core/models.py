from datetime import datetime, timezone
from typing import Any, TypeVar
from uuid import UUID, uuid4

from pydantic import TypeAdapter
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON, TypeDecorator
from sqlmodel import Field, SQLModel


T = TypeVar('T')


class PydanticJSON[T](TypeDecorator[T]):
    impl = JSON
    cache_ok = True

    def __init__(self, schema_type: Any):
        super().__init__()
        self._adapter = TypeAdapter(schema_type)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: T | None, dialect) -> Any:
        if value is None:
            return None

        validated_value = self._adapter.validate_python(value)
        return self._adapter.dump_python(validated_value, mode="json")

    def process_result_value(self, value: Any, dialect) -> T | None:
        if value is None:
            return None

        return self._adapter.validate_python(value)


class TableBase(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    deleted: bool = False
