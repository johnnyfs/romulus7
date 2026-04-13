from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.core.schemas import BaseDeleteResponse, BaseListItem, BaseListResponse, BaseModelResponse


class CommandExecutionSpec(BaseModel):
    kind: Literal["command"]
    commands: list[str]


ExecutionSpec = Annotated[CommandExecutionSpec, Field(discriminator="kind")]


class ExecutionBase(BaseModel):
    spec: ExecutionSpec


class ExecutionCreateRequest(ExecutionBase):
    pass


class ExecutionCreateResponse(BaseModelResponse, ExecutionBase):
    pass


class ExecutionListItem(BaseListItem, ExecutionBase):
    pass


class ExecutionListResponse(BaseListResponse[ExecutionListItem]):
    pass


class ExecutionDeleteResponse(BaseDeleteResponse):
    pass
