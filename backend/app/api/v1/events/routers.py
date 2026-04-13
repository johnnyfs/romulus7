from uuid import UUID

from fastapi import Depends, FastAPI, Query

from app.api.v1.events.models import EventRepository
from app.api.v1.events.schemas import EventCreateRequest, EventCreateResponse, EventListItem, EventListResponse
from app.core.config import settings
from common.events import EventSourceType

app = FastAPI()


@app.post("/")
async def create_event(
    request: EventCreateRequest,
    repository: EventRepository = Depends(EventRepository),
) -> EventCreateResponse:
    model = await repository.create(**request.model_dump())
    return EventCreateResponse(**model.model_dump())


@app.get("/")
async def get_events(
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, gt=0, le=settings.MAX_PAGE_SIZE),
    since: int | None = Query(None, ge=0),
    source_type: EventSourceType | None = None,
    source_id: UUID | None = None,
    repository: EventRepository = Depends(EventRepository),
) -> EventListResponse:
    models = await repository.list(
        limit=limit,
        since=since,
        source_type=source_type,
        source_id=source_id,
    )
    items = [EventListItem(**model.model_dump()) for model in models]
    return EventListResponse(items=items, count=len(items))
