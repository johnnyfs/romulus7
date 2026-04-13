import asyncio
import logging
from uuid import UUID

import asyncpg
from pydantic import BaseModel

from common.events import EventSourceType


logger = logging.getLogger(__name__)


class EventNotification(BaseModel):
    source_type: EventSourceType
    source_id: UUID


class PgNotifyBus:
    """
    Dedicated LISTEN/NOTIFY fan-out bus for SSE readers.

    Postgres LISTEN/NOTIFY only tells us that "something changed". The
    event rows still come from the append-only table, so subscribers wake
    up and then re-query the database for rows after their cursor.

    The same class can also deliver local wake-ups when Postgres isn't
    available, which keeps sqlite-based tests deterministic without
    changing the production architecture.
    """

    def __init__(self, *, dsn: str | None, channel: str):
        self._dsn = dsn
        self._channel = channel
        self._conn: asyncpg.Connection | None = None
        self._next_subscription_id = 0
        self._subscribers: dict[
            int,
            tuple[
                EventSourceType | None,
                UUID | None,
                asyncio.Queue[EventNotification],
            ],
        ] = {}

    @property
    def uses_database_notifications(self) -> bool:
        return bool(self._dsn and self._dsn.startswith("postgresql"))

    async def start(self) -> None:
        if not self.uses_database_notifications or self._conn is not None:
            return

        self._conn = await asyncpg.connect(self._dsn)
        await self._conn.add_listener(self._channel, self._on_notify)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.remove_listener(self._channel, self._on_notify)
            await self._conn.close()
            self._conn = None

        self._subscribers.clear()

    def subscribe(
        self,
        *,
        source_type: EventSourceType | None,
        source_id: UUID | None,
    ) -> tuple[int, asyncio.Queue[EventNotification]]:
        # One queued wake-up is enough because readers re-query the DB
        # until they have drained all rows after their cursor.
        queue: asyncio.Queue[EventNotification] = asyncio.Queue(maxsize=1)
        subscription_id = self._next_subscription_id
        self._next_subscription_id += 1
        self._subscribers[subscription_id] = (source_type, source_id, queue)
        return subscription_id, queue

    def unsubscribe(self, subscription_id: int) -> None:
        self._subscribers.pop(subscription_id, None)

    async def publish_local(self, notification: EventNotification) -> None:
        if self.uses_database_notifications:
            return

        self._fan_out(notification)

    def _on_notify(
        self,
        _connection: asyncpg.Connection,
        _pid: int,
        _channel: str,
        payload: str,
    ) -> None:
        try:
            notification = EventNotification.model_validate_json(payload)
        except Exception:
            logger.exception("Failed to parse event notification payload: %s", payload)
            return

        self._fan_out(notification)

    def _fan_out(self, notification: EventNotification) -> None:
        for source_type, source_id, queue in list(self._subscribers.values()):
            if source_type is not None and source_type != notification.source_type:
                continue
            if source_id is not None and source_id != notification.source_id:
                continue
            if queue.full():
                continue

            queue.put_nowait(notification)
