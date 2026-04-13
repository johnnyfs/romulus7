from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import StreamingResponse

from app.api.v1.events.controllers import EventsController
from app.api.v1.events.models import EventRepository
from app.api.v1.events.notify_bus import EventNotification, PgNotifyBus
from app.api.v1.events.schemas import EventCreateRequest, EventCreateResponse, EventListItem, EventListResponse
from app.api.v1.events.stream import event_stream_generator
from app.core.config import settings
from app.core.db import get_session_factory
from common.events import EventSourceType

app = FastAPI()
app.state.event_notify_bus = PgNotifyBus(dsn=None, channel=settings.EVENT_NOTIFY_CHANNEL)
app.state.event_session_factory = get_session_factory()


@app.post("/")
async def create_event(
    event_request: EventCreateRequest,
    request: Request,
    repository: EventRepository = Depends(EventRepository),
    controller: EventsController = Depends(EventsController),
) -> EventCreateResponse:
    model = await repository.create(**event_request.model_dump())
    await controller.handle_created_event(model)
    notify_bus: PgNotifyBus = request.app.state.event_notify_bus
    if not repository.uses_database_notifications():
        await notify_bus.publish_local(
            EventNotification(
                source_type=event_request.source_type,
                source_id=event_request.source_id,
            )
        )
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


@app.get("/stream")
async def stream_events(
    request: Request,
    since: int = Query(0, ge=0),
    after: int | None = Query(None, ge=0),
    source_type: EventSourceType | None = None,
    source_id: UUID | None = None,
) -> StreamingResponse:
    cursor = after if after is not None else since
    return StreamingResponse(
        event_stream_generator(
            since=cursor,
            source_type=source_type,
            source_id=source_id,
            session_factory=request.app.state.event_session_factory,
            notify_bus=request.app.state.event_notify_bus,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
