from typing import Any, Sequence
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

    async def list_by_execution_id(self, execution_id: UUID) -> Sequence[Dispatch]:
        statement = self._select().where(self._table_model.execution_id == execution_id)
        return (await self._session.exec(statement)).all()

    async def list_dispatch_ids_by_execution_ids(
        self,
        execution_ids: Sequence[UUID],
    ) -> dict[UUID, UUID]:
        if not execution_ids:
            return {}

        statement = self._select().where(self._table_model.execution_id.in_(execution_ids))
        models = (await self._session.exec(statement)).all()
        return {model.execution_id: model.id for model in models}
