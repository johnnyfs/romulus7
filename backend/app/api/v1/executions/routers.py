from uuid import UUID

from fastapi import Depends, FastAPI, Query

from app.api.v1.executions.models import ExecutionRepository
from app.api.v1.executions.schemas import (
    ExecutionCreateRequest,
    ExecutionCreateResponse,
    ExecutionDeleteResponse,
    ExecutionListItem,
    ExecutionListResponse,
)
from app.core.config import settings

app = FastAPI()


@app.post("/")
async def create_execution(
    request: ExecutionCreateRequest,
    repository: ExecutionRepository = Depends(ExecutionRepository),
) -> ExecutionCreateResponse:
    model = await repository.create(**request.model_dump())
    return ExecutionCreateResponse(**model.model_dump())


@app.get("/")
async def get_execution(
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, gt=0, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    repository: ExecutionRepository = Depends(ExecutionRepository),
) -> ExecutionListResponse:
    models = await repository.list(limit, offset)
    items = [ExecutionListItem(**model.model_dump()) for model in models]
    return ExecutionListResponse(items=items, count=len(items))


@app.get("/{execution_id}")
async def get_execution_by_id(
    execution_id: UUID,
    repository: ExecutionRepository = Depends(ExecutionRepository),
) -> ExecutionCreateResponse:
    model = await repository.get_by_id(execution_id)
    return ExecutionCreateResponse(**model.model_dump())


@app.delete("/{execution_id}")
async def delete_execution(
    execution_id: UUID,
    repository: ExecutionRepository = Depends(ExecutionRepository),
) -> ExecutionDeleteResponse:
    deleted = await repository.delete_by_id(execution_id)
    return ExecutionDeleteResponse(id=execution_id, deleted=deleted)
