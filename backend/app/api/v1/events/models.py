from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends
from sqlalchemy import DateTime, Enum, Integer, text
from sqlmodel import Column, Field, SQLModel, select

from app.api.v1.events.notify_bus import EventNotification
from app.api.v1.events.schemas import EventPayload
from app.core.config import settings
from app.core.db import get_session
from app.core.models import PydanticJSON
from common.events import DispatchEventType, EventSourceType


class Event(SQLModel, table=True):
    __tablename__ = "event"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    source_type: EventSourceType = Field(
        sa_column=Column(Enum(EventSourceType, native_enum=False), nullable=False)
    )
    source_id: UUID
    type: DispatchEventType = Field(
        sa_column=Column(Enum(DispatchEventType, native_enum=False), nullable=False)
    )
    payload: EventPayload = Field(sa_column=Column(PydanticJSON(EventPayload), nullable=False))
    deleted: bool = False


class EventRepository:
    def __init__(self, session=Depends(get_session)):
        self._session = session

    def _select(self):
        return select(Event).where(Event.deleted == False)  # noqa: E712

    def uses_database_notifications(self) -> bool:
        bind = self._session.get_bind()
        return bind is not None and bind.dialect.name == "postgresql"

    async def create(self, **kv_args) -> Event:
        model = Event(**kv_args)
        self._session.add(model)

        # The events table is the source of truth. We insert the row first,
        # then ask Postgres to send a small wake-up notification in the same
        # transaction. Postgres only delivers NOTIFY on commit, so SSE readers
        # never wake up before the append is durable.
        await self._session.flush()
        if self.uses_database_notifications():
            notification = EventNotification(
                source_type=model.source_type,
                source_id=model.source_id,
            )
            await self._session.execute(
                text("SELECT pg_notify(:channel, :payload)"),
                {
                    "channel": settings.EVENT_NOTIFY_CHANNEL,
                    "payload": notification.model_dump_json(),
                },
            )

        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def list(
        self,
        *,
        limit: int,
        since: int | None = None,
        source_type: EventSourceType | None = None,
        source_id: UUID | None = None,
    ) -> Sequence[Event]:
        statement = self._select()

        if since is not None:
            statement = statement.where(Event.id > since)

        if source_type is not None:
            statement = statement.where(Event.source_type == source_type)

        if source_id is not None:
            statement = statement.where(Event.source_id == source_id)

        statement = statement.order_by(Event.id).limit(limit or settings.DEFAULT_PAGE_SIZE)
        return (await self._session.exec(statement)).all()

    async def delete_by_dispatch_id(self, dispatch_id: UUID) -> int:
        statement = self._select().where(
            (Event.source_type == EventSourceType.DISPATCH) & (Event.source_id == dispatch_id)
        )
        events = (await self._session.exec(statement)).all()
        for event in events:
            event.deleted = True

        await self._session.commit()
        return len(events)
