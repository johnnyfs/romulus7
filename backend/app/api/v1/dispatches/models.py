from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlmodel import Column, Field

from app.core.db import get_session
from app.core.models import PydanticJSON, TableBase
from app.core.repositories import Repository


class Dispatch(TableBase, table=True):
    __tablename__ = 'dispatch'
    execution_id: UUID = Field(foreign_key="execution.id")
    worker_response: dict[str, Any] = Field(
        sa_column=Column(PydanticJSON(dict[str, Any]), nullable=False)
    )


class DispatchRepository(Repository[Dispatch]):
    def __init__(self, session = Depends(get_session)):
        super().__init__(table_model=Dispatch, session=session)
