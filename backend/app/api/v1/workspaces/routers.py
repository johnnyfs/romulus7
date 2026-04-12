from uuid import UUID

from fastapi import Depends, FastAPI, Query

from app.api.v1.workspaces.models import WorkspaceRepository
from app.api.v1.workspaces.schemas import WorkspaceCreateRequest, WorkspaceCreateResponse, WorkspaceDeleteResponse, WorkspaceListItem, WorkspaceListResponse

from app.core.config import settings

app = FastAPI()

@app.post("/")
async def create_workspace(
    request: WorkspaceCreateRequest,
    repository: WorkspaceRepository = Depends(WorkspaceRepository),
) -> WorkspaceCreateResponse:
    model = await repository.create(**request.model_dump())
    return WorkspaceCreateResponse(**model.model_dump())

@app.get("/")
async def get_workspace(
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, gt=0, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    repository: WorkspaceRepository = Depends(WorkspaceRepository),
) -> WorkspaceListResponse:
    models = await repository.list(limit, offset)
    items = [WorkspaceListItem(**model.model_dump()) for model in models]
    return WorkspaceListResponse(items=items, count=len(items))

@app.get("/{workspace_id}")
async def get_workspace_by_id(
    workspace_id: UUID,
    repository: WorkspaceRepository = Depends(WorkspaceRepository),
) -> WorkspaceCreateResponse:
    model = await repository.get_by_id(workspace_id)
    return WorkspaceCreateResponse(**model.model_dump())

@app.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: UUID,
    repository: WorkspaceRepository = Depends(WorkspaceRepository),
) -> WorkspaceDeleteResponse:
    deleted = await repository.delete_by_id(workspace_id)
    return WorkspaceDeleteResponse(id=workspace_id, deleted=deleted)