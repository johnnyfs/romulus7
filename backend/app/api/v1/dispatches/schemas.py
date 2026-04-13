from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import BaseModelResponse


class DispatchCreateResponse(BaseModelResponse):
    execution_id: UUID
    worker_response: dict[str, Any]
