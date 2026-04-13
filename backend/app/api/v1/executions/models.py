from sqlmodel import Column, Field

from app.api.v1.executions.schemas import ExecutionSpec
from app.core.db import get_session
from app.core.models import PydanticJSON, TableBase
from app.core.repositories import Repository
from fastapi import Depends


class Execution(TableBase, table=True):
    __tablename__ = 'execution'
    spec: ExecutionSpec = Field(sa_column=Column(PydanticJSON(ExecutionSpec), nullable=False))


class ExecutionRepository(Repository[Execution]):
    def __init__(self, session = Depends(get_session)):
        super().__init__(table_model=Execution, session=session)
