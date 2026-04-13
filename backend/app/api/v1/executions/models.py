from typing import Any

from sqlmodel import Column, Field

from app.core.db import get_session
from app.core.models import PydanticJSON, TableBase
from app.core.repositories import Repository
from common.execution import ExecutionSpec
from fastapi import Depends


class Execution(TableBase, table=True):
    __tablename__ = "execution"
    name: str
    spec: ExecutionSpec = Field(sa_column=Column(PydanticJSON(ExecutionSpec), nullable=False))
    metadata_: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column("metadata", PydanticJSON(dict[str, Any]), nullable=True),
    )


class ExecutionRepository(Repository[Execution]):
    def __init__(self, session=Depends(get_session)):
        super().__init__(table_model=Execution, session=session)
