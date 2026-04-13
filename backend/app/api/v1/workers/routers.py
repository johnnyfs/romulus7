from uuid import UUID

from fastapi import Depends, FastAPI, Query

from app.api.v1.sandboxes.models import SandboxRepository
from app.api.v1.worker_leases.models import WorkerLeaseRepository
from app.api.v1.worker_leases.schemas import WorkerLeaseCreateRequest, WorkerLeaseCreateResponse, WorkerLeaseListItem
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


async def serialize_worker(
    model,
    worker_lease_repository: WorkerLeaseRepository,
) -> WorkerCreateResponse:
    leases_by_worker_id = await worker_lease_repository.list_with_sandbox_names_by_worker_ids(
        [model.id]
    )
    leases = [
        WorkerLeaseListItem(**lease.model_dump(), sandbox_name=sandbox_name)
        for lease, sandbox_name in leases_by_worker_id.get(model.id, [])
    ]
    return WorkerCreateResponse(**model.model_dump(), leases=leases)


@app.post("/")
async def create_worker(
    request: WorkerCreateRequest,
    repository: WorkerRepository = Depends(WorkerRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
) -> WorkerCreateResponse:
    model = await repository.create(**request.model_dump())
    return await serialize_worker(model, worker_lease_repository)


@app.get("/")
async def get_worker(
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, gt=0, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    repository: WorkerRepository = Depends(WorkerRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
) -> WorkerListResponse:
    models = await repository.list(limit, offset)
    leases_by_worker_id = await worker_lease_repository.list_with_sandbox_names_by_worker_ids(
        [model.id for model in models]
    )
    items = [
        WorkerListItem(
            **model.model_dump(),
            leases=[
                WorkerLeaseListItem(**lease.model_dump(), sandbox_name=sandbox_name)
                for lease, sandbox_name in leases_by_worker_id.get(model.id, [])
            ],
        )
        for model in models
    ]
    return WorkerListResponse(items=items, count=len(items))


@app.get("/{worker_id}")
async def get_worker_by_id(
    worker_id: UUID,
    repository: WorkerRepository = Depends(WorkerRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
) -> WorkerCreateResponse:
    model = await repository.get_by_id(worker_id)
    return await serialize_worker(model, worker_lease_repository)


@app.post("/{worker_id}/lease")
async def create_worker_lease(
    worker_id: UUID,
    request: WorkerLeaseCreateRequest,
    repository: WorkerRepository = Depends(WorkerRepository),
    sandbox_repository: SandboxRepository = Depends(SandboxRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
) -> WorkerLeaseCreateResponse:
    await repository.get_by_id(worker_id)
    sandbox = await sandbox_repository.get_by_id(request.sandbox_id)
    model = await worker_lease_repository.create_for_worker(
        worker_id=worker_id,
        sandbox_id=request.sandbox_id,
    )
    return WorkerLeaseCreateResponse(
        **model.model_dump(),
        sandbox_name=sandbox.name,
    )


@app.post("/{worker_id}/heartbeat")
async def heartbeat_worker(
    worker_id: UUID,
    repository: WorkerRepository = Depends(WorkerRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
) -> WorkerCreateResponse:
    model = await repository.heartbeat_by_id(worker_id)
    return await serialize_worker(model, worker_lease_repository)


@app.delete("/{worker_id}")
async def delete_worker(
    worker_id: UUID,
    repository: WorkerRepository = Depends(WorkerRepository),
) -> WorkerDeleteResponse:
    deleted = await repository.delete_by_id(worker_id)
    return WorkerDeleteResponse(id=worker_id, deleted=deleted)
