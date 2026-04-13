from pathlib import PurePath
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CommandExecutionSpec(BaseModel):
    kind: Literal["command"]
    commands: list[str] = Field(min_length=1)


ExecutionSpec = Annotated[CommandExecutionSpec, Field(discriminator="kind")]


class DispatchRequest(BaseModel):
    sandbox_id: UUID | None = None
    working_directory: str | None = None
    execution_spec: ExecutionSpec

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
