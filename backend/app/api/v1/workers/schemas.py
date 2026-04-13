from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import AnyHttpUrl, BaseModel, BeforeValidator, Field, TypeAdapter, WithJsonSchema

from app.core.schemas import BaseDeleteResponse, BaseListItem, BaseListResponse, BaseModelResponse


_worker_url_adapter = TypeAdapter(AnyHttpUrl)


def validate_worker_url(value: Any) -> str:
    return str(_worker_url_adapter.validate_python(value))


WorkerURL = Annotated[
    str,
    BeforeValidator(validate_worker_url),
    WithJsonSchema({"type": "string", "format": "uri"}),
]


class LocalWorker(BaseModel):
    kind: Literal["local"]
    url: WorkerURL


WorkerType = Annotated[LocalWorker, Field(discriminator="kind")]


class WorkerBase(BaseModel):
    url: WorkerURL


class WorkerCreateRequest(WorkerBase):
    pass


class WorkerRead(BaseModel):
    heartbeat_at: datetime | None = None


class WorkerCreateResponse(BaseModelResponse, WorkerBase, WorkerRead):
    pass


class WorkerListItem(BaseListItem, WorkerBase, WorkerRead):
    pass


class WorkerListResponse(BaseListResponse[WorkerListItem]):
    pass


class WorkerDeleteResponse(BaseDeleteResponse):
    pass
