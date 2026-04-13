from typing import Annotated, Literal

from pydantic import BaseModel, Field
from enum import StrEnum


class EventSourceType(StrEnum):
    DISPATCH = "dispatch"


class DispatchEventType(StrEnum):
    COMMAND_STDOUT = "command.stdout"


class CommandStdoutEventPayload(BaseModel):
    kind: Literal["command.stdout"] = DispatchEventType.COMMAND_STDOUT
    line: str


EventPayload = Annotated[CommandStdoutEventPayload, Field(discriminator="kind")]
