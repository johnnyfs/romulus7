from pathlib import PurePath
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.core.schemas import BaseDeleteResponse, BaseListItem, BaseListResponse, BaseModelResponse
from common.execution import ExecutionSpec


class ExecutionBase(BaseModel):
    spec: ExecutionSpec


class ExecutionCreateRequest(ExecutionBase):
    pass


class ExecutionDispatchRequest(BaseModel):
    sandbox_id: UUID | None = None
    working_directory: str | None = None

    @field_validator("working_directory")
    @classmethod
    def validate_working_directory(cls, value: str | None) -> str | None:
        if value in (None, "", "."):
            return None

        path = PurePath(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("working_directory must be a relative path")

        return str(path)


class ExecutionCreateResponse(BaseModelResponse, ExecutionBase):
    pass


class ExecutionListItem(BaseListItem, ExecutionBase):
    pass


class ExecutionListResponse(BaseListResponse[ExecutionListItem]):
    pass


class ExecutionDeleteResponse(BaseDeleteResponse):
    pass
