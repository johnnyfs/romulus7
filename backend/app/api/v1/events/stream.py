"""
SSE streaming generator for the event stream.

The append-only events table is the source of truth. LISTEN/NOTIFY is only
used as a wake-up signal so readers know when to run a fresh query for rows
after their last seen cursor. We never rely on a long-running SQL query or
trust the NOTIFY payload as the event data itself.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.events.models import Event, EventRepository
from app.api.v1.events.notify_bus import PgNotifyBus
from app.core.config import settings
from common.events import EventSourceType


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


async def _load_events(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    cursor: int,
    source_type: EventSourceType | None,
    source_id: UUID | None,
) -> list[Event]:
    async with session_factory() as session:
        repository = EventRepository(session=session)
        events = await repository.list(
            limit=settings.EVENT_STREAM_BATCH_SIZE,
            since=cursor,
            source_type=source_type,
            source_id=source_id,
        )
        return list(events)


async def event_stream_generator(
    *,
    since: int,
    session_factory: async_sessionmaker[AsyncSession],
    notify_bus: PgNotifyBus,
    source_type: EventSourceType | None = None,
    source_id: UUID | None = None,
) -> AsyncGenerator[str, None]:
    cursor = since

    async def emit_available_rows(available_events: list[Event]) -> AsyncGenerator[str, None]:
        nonlocal cursor
        for event in available_events:
            yield f"data: {_serialize_event(event)}\n\n"
            cursor = event.id  # type: ignore[assignment]

    while True:
        events = await _load_events(
            session_factory=session_factory,
            cursor=cursor,
            source_type=source_type,
            source_id=source_id,
        )
        if not events:
            break

        async for chunk in emit_available_rows(events):
            yield chunk

    subscription_id, queue = notify_bus.subscribe(
        source_type=source_type,
        source_id=source_id,
    )

    try:
        while True:
            # Close the gap between the backlog query and subscription
            # registration. The DB stays authoritative, so we immediately
            # re-query before blocking on the next wake-up.
            events = await _load_events(
                session_factory=session_factory,
                cursor=cursor,
                source_type=source_type,
                source_id=source_id,
            )
            if events:
                async for chunk in emit_available_rows(events):
                    yield chunk
                continue

            try:
                await asyncio.wait_for(
                    queue.get(),
                    timeout=settings.EVENT_STREAM_KEEPALIVE_SECONDS,
                )
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue

            # NOTIFY wakes the stream, but the rows still come from the
            # append-only table so ordering and cursors come from Event.id.
            while True:
                events = await _load_events(
                    session_factory=session_factory,
                    cursor=cursor,
                    source_type=source_type,
                    source_id=source_id,
                )
                if not events:
                    break

                async for chunk in emit_available_rows(events):
                    yield chunk
    finally:
        notify_bus.unsubscribe(subscription_id)
