from uuid import UUID

from fastapi import Depends

from app.api.v1.dispatches.models import DispatchRepository
from app.api.v1.events.models import EventRepository
from common.events import DispatchEventType, EventSourceType


class EventsController:
    def __init__(
        self,
        event_repository: EventRepository = Depends(EventRepository),
        dispatch_repository: DispatchRepository = Depends(DispatchRepository),
    ):
        self._event_repository = event_repository
        self._dispatch_repository = dispatch_repository

    async def handle_created_event(self, event) -> None:
        if (
            event.source_type == EventSourceType.DISPATCH
            and event.type == DispatchEventType.DISPATCH_TERMINATED
        ):
            await self._dispatch_repository.mark_terminated(event.source_id)

    async def delete_by_dispatch_id(self, dispatch_id: UUID) -> int:
        return await self._event_repository.delete_by_dispatch_id(dispatch_id)


class DispatchesController:
    def __init__(
        self,
        dispatch_repository: DispatchRepository = Depends(DispatchRepository),
        events_controller: EventsController = Depends(EventsController),
    ):
        self._dispatch_repository = dispatch_repository
        self._events_controller = events_controller

    async def delete(self, dispatch_id: UUID) -> bool:
        await self._events_controller.delete_by_dispatch_id(dispatch_id)
        return await self._dispatch_repository.delete_by_id(dispatch_id)
