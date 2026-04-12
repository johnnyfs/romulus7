from datetime import datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


class BaseListItem(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted: bool = Field(exclude=True)


class BaseModelResponse(BaseListItem):
    pass


T = TypeVar('T', bound=BaseListItem)
class BaseListResponse[T](BaseModel):
    items: list[T]
    count: int
    next: str | None

class BaseDeleteResponse(BaseModel):
    id: UUID
    deleted: bool