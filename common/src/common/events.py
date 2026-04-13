from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field
from enum import StrEnum


class EventSourceType(StrEnum):
    DISPATCH = "dispatch"


class DispatchEventType(StrEnum):
    COMMAND_STDOUT = "command.stdout"
    COMMAND_EXIT = "command.exit"
    DISPATCH_TERMINATED = "dispatch.terminated"


EventCallback = dict[str, Any]


class CommandStdoutEventPayload(BaseModel):
    kind: Literal["command.stdout"] = DispatchEventType.COMMAND_STDOUT
    line: str
    callback: EventCallback | None = None


class CommandExitEventPayload(BaseModel):
    kind: Literal["command.exit"] = DispatchEventType.COMMAND_EXIT
    exit_code: int
    callback: EventCallback | None = None


class DispatchTerminatedEventPayload(BaseModel):
    kind: Literal["dispatch.terminated"] = DispatchEventType.DISPATCH_TERMINATED
    callback: EventCallback | None = None


EventPayload = Annotated[
    CommandStdoutEventPayload | CommandExitEventPayload | DispatchTerminatedEventPayload,
    Field(discriminator="kind"),
]
