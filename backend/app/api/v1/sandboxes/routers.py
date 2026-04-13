from uuid import UUID

from fastapi import Depends, FastAPI, Query

from app.api.v1.sandboxes.models import SandboxRepository
from app.api.v1.sandboxes.schemas import (
    SandboxCreateRequest,
    SandboxCreateResponse,
    SandboxDeleteResponse,
    SandboxListItem,
    SandboxListResponse,
)
from app.api.v1.worker_leases.models import WorkerLeaseRepository
from app.core.config import settings

app = FastAPI()


async def serialize_sandbox(
    model,
    worker_lease_repository: WorkerLeaseRepository,
) -> SandboxCreateResponse:
    worker_lease_ids_by_sandbox_id = await worker_lease_repository.list_worker_lease_ids_by_sandbox_ids(
        [model.id]
    )
    return SandboxCreateResponse(
        **model.model_dump(),
        worker_lease_id=worker_lease_ids_by_sandbox_id.get(model.id),
    )


@app.post("/")
async def create_sandbox(
    request: SandboxCreateRequest,
    repository: SandboxRepository = Depends(SandboxRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
) -> SandboxCreateResponse:
    model = await repository.create(**request.model_dump())
    return await serialize_sandbox(model, worker_lease_repository)


@app.get("/")
async def get_sandbox(
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, gt=0, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    repository: SandboxRepository = Depends(SandboxRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
) -> SandboxListResponse:
    models = await repository.list(limit, offset)
    worker_lease_ids_by_sandbox_id = await worker_lease_repository.list_worker_lease_ids_by_sandbox_ids(
        [model.id for model in models]
    )
    items = [
        SandboxListItem(
            **model.model_dump(),
            worker_lease_id=worker_lease_ids_by_sandbox_id.get(model.id),
        )
        for model in models
    ]
    return SandboxListResponse(items=items, count=len(items))


@app.get("/{sandbox_id}")
async def get_sandbox_by_id(
    sandbox_id: UUID,
    repository: SandboxRepository = Depends(SandboxRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
) -> SandboxCreateResponse:
    model = await repository.get_by_id(sandbox_id)
    return await serialize_sandbox(model, worker_lease_repository)


@app.delete("/{sandbox_id}")
async def delete_sandbox(
    sandbox_id: UUID,
    repository: SandboxRepository = Depends(SandboxRepository),
) -> SandboxDeleteResponse:
    deleted = await repository.delete_by_id(sandbox_id)
    return SandboxDeleteResponse(id=sandbox_id, deleted=deleted)
