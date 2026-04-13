"""
SSE streaming generator for the event stream.

Yields events as Server-Sent Events, polling the database for new rows.
Manages its own DB sessions since the connection is long-lived and can't
use FastAPI's request-scoped dependency injection.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.events.models import Event
from app.core.config import settings
from common.events import EventSourceType

_engine = create_async_engine(settings.DATABASE_URL, echo=settings.ECHO_SQL)
_make_session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

POLL_INTERVAL_SECONDS = 1
BATCH_LIMIT = 100


def _serialize_event(event: Event) -> str:
    data = {
        "id": event.id,
        "created_at": event.created_at.isoformat() if isinstance(event.created_at, datetime) else str(event.created_at),
        "source_type": str(event.source_type),
        "source_id": str(event.source_id),
        "type": str(event.type),
        "payload": event.payload.model_dump(mode="json"),
    }
    return json.dumps(data, separators=(",", ":"))


async def event_stream_generator(
    *,
    since: int,
    source_type: EventSourceType | None = None,
    source_id: UUID | None = None,
) -> AsyncGenerator[str, None]:
    cursor = since

    while True:
        async with _make_session() as session:
            statement = select(Event).where(Event.id > cursor)

            if source_type is not None:
                statement = statement.where(Event.source_type == source_type)
            if source_id is not None:
                statement = statement.where(Event.source_id == source_id)

            statement = statement.order_by(Event.id).limit(BATCH_LIMIT)
            events = (await session.exec(statement)).all()

        for event in events:
            yield f"data: {_serialize_event(event)}\n\n"
            cursor = event.id  # type: ignore[assignment]

        if not events:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
