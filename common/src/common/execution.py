from typing import Annotated, Literal

from pydantic import BaseModel, Field


class CommandExecutionSpec(BaseModel):
    kind: Literal["command"]
    commands: list[str] = Field(min_length=1)


ExecutionSpec = Annotated[CommandExecutionSpec, Field(discriminator="kind")]
