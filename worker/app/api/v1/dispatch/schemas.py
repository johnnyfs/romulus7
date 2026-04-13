from pathlib import PurePath
from uuid import UUID

from pydantic import BaseModel, field_validator

from common.execution import ExecutionSpec
from common.events import EventCallback


class DispatchRequest(BaseModel):
    sandbox_id: UUID | None = None
    working_directory: str | None = None
    execution_spec: ExecutionSpec
    callback: EventCallback | None = None

    @field_validator("working_directory")
    @classmethod
    def validate_working_directory(cls, value: str | None) -> str | None:
        if value in (None, "", "."):
            return None

        path = PurePath(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("working_directory must be a relative path")

        return str(path)


class DispatchResponse(BaseModel):
    id: UUID
    process_id: int
