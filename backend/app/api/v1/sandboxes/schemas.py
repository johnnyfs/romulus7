from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import BaseDeleteResponse, BaseListItem, BaseListResponse, BaseModelResponse


class SandboxBase(BaseModel):
    name: str


class SandboxCreateRequest(SandboxBase):
    pass


class SandboxRead(BaseModel):
    worker_lease_id: UUID | None = None


class SandboxCreateResponse(BaseModelResponse, SandboxBase, SandboxRead):
    pass


class SandboxListItem(BaseListItem, SandboxBase, SandboxRead):
    pass


class SandboxListResponse(BaseListResponse[SandboxListItem]):
    pass


class SandboxDeleteResponse(BaseDeleteResponse):
    pass
