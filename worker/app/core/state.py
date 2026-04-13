import asyncio
from dataclasses import dataclass, field
from uuid import UUID

from common.events import EventCallback


@dataclass(slots=True)
class WorkerState:
    id: UUID | None = None
    commands: dict[UUID, int] = field(default_factory=dict)
    command_tasks: dict[UUID, asyncio.Task[None]] = field(default_factory=dict)
    callbacks: dict[UUID, EventCallback] = field(default_factory=dict)


worker_state = WorkerState()
