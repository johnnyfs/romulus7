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
    terminated: bool = False
    worker_response: dict[str, Any] = Field(
        sa_column=Column(PydanticJSON(dict[str, Any]), nullable=False)
    )


class DispatchRepository(Repository[Dispatch]):
    def __init__(self, session = Depends(get_session)):
        super().__init__(table_model=Dispatch, session=session)

    async def list(
        self,
        limit: int,
        offset: int = 0,
        terminated: bool | None = None,
    ) -> Sequence[Dispatch]:
        statement = self._list(offset, limit)
        if terminated is not None:
            statement = statement.where(self._table_model.terminated == terminated)
        return (await self._session.exec(statement)).all()

    async def list_by_execution_id(self, execution_id: UUID) -> Sequence[Dispatch]:
        statement = self._select().where(self._table_model.execution_id == execution_id)
        return (await self._session.exec(statement)).all()

    async def mark_terminated(self, dispatch_id: UUID) -> Dispatch | None:
        model = await self.find_by_id(dispatch_id)
        if not model:
            return None

        model.terminated = True
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def list_dispatch_ids_by_execution_ids(
        self,
        execution_ids: Sequence[UUID],
    ) -> dict[UUID, UUID]:
        if not execution_ids:
            return {}

        statement = self._select().where(self._table_model.execution_id.in_(execution_ids))
        models = (await self._session.exec(statement)).all()
        return {model.execution_id: model.id for model in models}
