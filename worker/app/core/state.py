from dataclasses import dataclass, field
from uuid import UUID


@dataclass(slots=True)
class WorkerState:
    id: UUID | None = None
    commands: dict[UUID, int] = field(default_factory=dict)


worker_state = WorkerState()
