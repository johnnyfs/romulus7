from typing import Any
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, Query
from fastapi import HTTPException

from app.api.v1.dispatches.models import DispatchRepository
from app.api.v1.dispatches.schemas import DispatchCreateResponse
from app.api.v1.executions.controllers import ExecutionsController
from app.api.v1.sandboxes.models import SandboxRepository
from app.api.v1.worker_leases.models import WorkerLeaseRepository
from app.api.v1.workers.models import WorkerRepository
from app.api.v1.executions.models import ExecutionRepository
from app.api.v1.executions.schemas import (
    ExecutionCreateRequest,
    ExecutionCreateResponse,
    ExecutionDispatchRequest,
    ExecutionDeleteResponse,
    ExecutionListItem,
    ExecutionListResponse,
)
from app.core.config import settings

app = FastAPI()


async def dispatch_to_worker(
    worker_url: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(base_url=worker_url) as client:
            response = await client.post("/api/v1/dispatch/", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"worker dispatch failed for {worker_url}") from exc


async def get_worker_for_execution_dispatch(
    sandbox_id: UUID | None,
    worker_repository: WorkerRepository,
    sandbox_repository: SandboxRepository,
    worker_lease_repository: WorkerLeaseRepository,
):
    if sandbox_id is None:
        maybe_worker = await worker_repository.find_first()
        if not maybe_worker:
            raise HTTPException(status_code=409, detail="no workers available to dispatch execution")
        return maybe_worker

    await sandbox_repository.get_by_id(sandbox_id)
    maybe_existing_lease = await worker_lease_repository.find_by_sandbox_id(sandbox_id)
    if maybe_existing_lease:
        return await worker_repository.get_by_id(maybe_existing_lease.worker_id)

    maybe_worker = await worker_repository.find_first()
    if not maybe_worker:
        raise HTTPException(status_code=409, detail="no workers available to dispatch execution")

    await worker_lease_repository.create_for_worker(
        worker_id=maybe_worker.id,
        sandbox_id=sandbox_id,
    )
    return maybe_worker


@app.post("/")
async def create_execution(
    request: ExecutionCreateRequest,
    repository: ExecutionRepository = Depends(ExecutionRepository),
) -> ExecutionCreateResponse:
    data = request.model_dump()
    data["metadata_"] = data.pop("metadata", None)
    model = await repository.create(**data)
    resp = model.model_dump()
    resp["metadata"] = resp.pop("metadata_", None)
    return ExecutionCreateResponse(**resp)


@app.get("/")
async def get_execution(
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, gt=0, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    repository: ExecutionRepository = Depends(ExecutionRepository),
    dispatch_repository: DispatchRepository = Depends(DispatchRepository),
) -> ExecutionListResponse:
    models = await repository.list(limit, offset)
    dispatch_ids_by_execution_id = await dispatch_repository.list_dispatch_ids_by_execution_ids(
        [model.id for model in models]
    )
    items = []
    for model in models:
        data = model.model_dump()
        data["metadata"] = data.pop("metadata_", None)
        data["dispatch_id"] = dispatch_ids_by_execution_id.get(model.id)
        items.append(ExecutionListItem(**data))
    return ExecutionListResponse(items=items, count=len(items))


@app.get("/{execution_id}")
async def get_execution_by_id(
    execution_id: UUID,
    repository: ExecutionRepository = Depends(ExecutionRepository),
) -> ExecutionCreateResponse:
    model = await repository.get_by_id(execution_id)
    resp = model.model_dump()
    resp["metadata"] = resp.pop("metadata_", None)
    return ExecutionCreateResponse(**resp)


@app.post("/{execution_id}/dispatch")
async def dispatch_execution(
    execution_id: UUID,
    request: ExecutionDispatchRequest,
    repository: ExecutionRepository = Depends(ExecutionRepository),
    worker_repository: WorkerRepository = Depends(WorkerRepository),
    sandbox_repository: SandboxRepository = Depends(SandboxRepository),
    worker_lease_repository: WorkerLeaseRepository = Depends(WorkerLeaseRepository),
    dispatch_repository: DispatchRepository = Depends(DispatchRepository),
) -> DispatchCreateResponse:
    execution = await repository.get_by_id(execution_id)
    worker = await get_worker_for_execution_dispatch(
        sandbox_id=request.sandbox_id,
        worker_repository=worker_repository,
        sandbox_repository=sandbox_repository,
        worker_lease_repository=worker_lease_repository,
    )
    worker_response = await dispatch_to_worker(
        worker.url,
        payload={
            "sandbox_id": str(request.sandbox_id) if request.sandbox_id else None,
            "working_directory": request.working_directory,
            "execution_spec": execution.model_dump()["spec"],
            "callback": request.callback,
        },
    )
    model = await dispatch_repository.create(
        id=UUID(worker_response["id"]),
        execution_id=execution.id,
        worker_response=worker_response,
    )
    return DispatchCreateResponse(**model.model_dump())


@app.delete("/{execution_id}")
async def delete_execution(
    execution_id: UUID,
    controller: ExecutionsController = Depends(ExecutionsController),
) -> ExecutionDeleteResponse:
    deleted = await controller.delete(execution_id)
    return ExecutionDeleteResponse(id=execution_id, deleted=deleted)
