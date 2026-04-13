from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import BaseListItem, BaseModelResponse


class WorkerLeaseCreateRequest(BaseModel):
    sandbox_id: UUID


class WorkerLeaseBase(BaseModel):
    worker_id: UUID
    sandbox_id: UUID


class WorkerLeaseRead(BaseModel):
    sandbox_name: str


class WorkerLeaseCreateResponse(BaseModelResponse, WorkerLeaseBase, WorkerLeaseRead):
    pass


class WorkerLeaseListItem(BaseListItem, WorkerLeaseBase, WorkerLeaseRead):
    pass
