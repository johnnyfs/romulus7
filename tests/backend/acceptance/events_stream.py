import asyncio
import json
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.events.routers import app as events_app
from app.api.v1.events.stream import event_stream_generator
from common.events import EventSourceType


pytestmark = pytest.mark.asyncio


async def test_event_stream_sends_backlog_and_requeries_after_notify(
    create_event,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    source_id = str(uuid4())
    notify_bus = events_app.state.event_notify_bus
    events_app.state.event_session_factory = session_factory

    first_event = await create_event(
        {
            "source_type": "dispatch",
            "source_id": source_id,
            "type": "command.stdout",
            "payload": {
                "kind": "command.stdout",
                "line": "alpha",
            },
        }
    )

    generator = event_stream_generator(
        since=0,
        session_factory=session_factory,
        notify_bus=notify_bus,
        source_type=EventSourceType.DISPATCH,
        source_id=UUID(first_event["source_id"]),
    )

    try:
        first_chunk = await asyncio.wait_for(generator.__anext__(), timeout=1)
        first_payload = json.loads(first_chunk.removeprefix("data: ").strip())
        assert first_payload["id"] == first_event["id"]
        assert first_payload["payload"]["line"] == "alpha"

        next_chunk_task = asyncio.create_task(generator.__anext__())

        for _ in range(100):
            if notify_bus._subscribers:
                break
            await asyncio.sleep(0.01)
        else:
            raise AssertionError("stream generator did not subscribe to notifications")

        second_event = await create_event(
            {
                "source_type": "dispatch",
                "source_id": source_id,
                "type": "command.stdout",
                "payload": {
                    "kind": "command.stdout",
                    "line": "beta",
                },
            }
        )

        second_chunk = await asyncio.wait_for(next_chunk_task, timeout=1)
        second_payload = json.loads(second_chunk.removeprefix("data: ").strip())
        assert second_payload["id"] == second_event["id"]
        assert second_payload["payload"]["line"] == "beta"
    finally:
        await generator.aclose()
