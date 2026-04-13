from uuid import UUID

from fastapi import Depends, FastAPI, Query

from app.api.v1.workers.models import WorkerRepository
from app.api.v1.workers.schemas import (
    WorkerCreateRequest,
    WorkerCreateResponse,
    WorkerDeleteResponse,
    WorkerListItem,
    WorkerListResponse,
)
from app.core.config import settings

app = FastAPI()


@app.post("/")
async def create_worker(
    request: WorkerCreateRequest,
    repository: WorkerRepository = Depends(WorkerRepository),
) -> WorkerCreateResponse:
    model = await repository.create(**request.model_dump())
    return WorkerCreateResponse(**model.model_dump())


@app.get("/")
async def get_worker(
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, gt=0, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    repository: WorkerRepository = Depends(WorkerRepository),
) -> WorkerListResponse:
    models = await repository.list(limit, offset)
    items = [WorkerListItem(**model.model_dump()) for model in models]
    return WorkerListResponse(items=items, count=len(items))


@app.get("/{worker_id}")
async def get_worker_by_id(
    worker_id: UUID,
    repository: WorkerRepository = Depends(WorkerRepository),
) -> WorkerCreateResponse:
    model = await repository.get_by_id(worker_id)
    return WorkerCreateResponse(**model.model_dump())


@app.post("/{worker_id}/heartbeat")
async def heartbeat_worker(
    worker_id: UUID,
    repository: WorkerRepository = Depends(WorkerRepository),
) -> WorkerCreateResponse:
    model = await repository.heartbeat_by_id(worker_id)
    return WorkerCreateResponse(**model.model_dump())


@app.delete("/{worker_id}")
async def delete_worker(
    worker_id: UUID,
    repository: WorkerRepository = Depends(WorkerRepository),
) -> WorkerDeleteResponse:
    deleted = await repository.delete_by_id(worker_id)
    return WorkerDeleteResponse(id=worker_id, deleted=deleted)
