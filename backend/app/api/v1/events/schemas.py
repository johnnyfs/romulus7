from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, model_validator
from common.events import DispatchEventType, EventPayload, EventSourceType


class EventBase(BaseModel):
    source_type: EventSourceType
    source_id: UUID
    type: DispatchEventType
    payload: EventPayload

    @model_validator(mode="after")
    def validate_type_matches_payload(self):
        if self.type != self.payload.kind:
            raise ValueError("type must match payload kind")

        return self


class EventCreateRequest(EventBase):
    pass


class EventCreateResponse(EventBase):
    id: int
    created_at: datetime


class EventListItem(EventCreateResponse):
    pass


class EventListResponse(BaseModel):
    items: list[EventListItem]
    count: int
