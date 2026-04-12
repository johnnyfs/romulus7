from pydantic import BaseModel

from app.core.schemas import BaseDeleteResponse, BaseListItem, BaseListResponse, BaseModelResponse

class WorkspaceBase(BaseModel):
    name: str

class WorkspaceCreateRequest(WorkspaceBase):
    pass

class WorkspaceCreateResponse(BaseModelResponse, WorkspaceBase):
    pass

class WorkspaceListItem(BaseListItem, WorkspaceBase):
    pass

class WorkspaceListResponse(BaseListResponse[WorkspaceListItem]):
    pass

class WorkspaceDeleteResponse(BaseDeleteResponse):
    pass