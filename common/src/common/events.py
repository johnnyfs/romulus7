from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field
from enum import StrEnum


class EventSourceType(StrEnum):
    DISPATCH = "dispatch"


class DispatchEventType(StrEnum):
    COMMAND_STDOUT = "command.stdout"


EventCallback = dict[str, Any]


class CommandStdoutEventPayload(BaseModel):
    kind: Literal["command.stdout"] = DispatchEventType.COMMAND_STDOUT
    line: str
    callback: EventCallback | None = None


EventPayload = Annotated[CommandStdoutEventPayload, Field(discriminator="kind")]
