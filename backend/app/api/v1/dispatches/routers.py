from fastapi import Depends, FastAPI, Query

from app.api.v1.dispatches.models import DispatchRepository
from app.api.v1.dispatches.schemas import DispatchListItem, DispatchListResponse
from app.core.config import settings

app = FastAPI()


@app.get("/")
async def get_dispatches(
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, gt=0, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    terminated: bool | None = None,
    repository: DispatchRepository = Depends(DispatchRepository),
) -> DispatchListResponse:
    models = await repository.list(limit=limit, offset=offset, terminated=terminated)
    items = [DispatchListItem(**model.model_dump()) for model in models]
    return DispatchListResponse(items=items, count=len(items))
