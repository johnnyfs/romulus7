from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class CommandExecutionSpec(BaseModel):
    kind: Literal["command"]
    command: str = Field(min_length=1)

    @field_validator("command")
    @classmethod
    def validate_command(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("command must not be empty")
        return normalized


ExecutionSpec = Annotated[CommandExecutionSpec, Field(discriminator="kind")]
