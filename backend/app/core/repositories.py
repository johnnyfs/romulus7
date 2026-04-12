from typing import Sequence, Type, TypeVar
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.models import TableBase

T = TypeVar('T', bound=TableBase)

class Repository[T]:
    def __init__(self, table_model: Type[T], session: AsyncSession):
        self._table_model = table_model
        self._session = session

    def _select(self):
        return select(self._table_model).where(self._table_model.deleted == False)  # noqa: E712

    def _list(self, offset: int, limit: int):
        return self._select().offset(offset).limit(limit)
    
    def _get(self, id: UUID):
        return self._select().where(self._table_model.id == id)
    
    async def create(self, **kv_args) -> T:
        model = self._table_model(**kv_args)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model
    
    async def list(self, limit: int, offset: int = 0) -> Sequence[T]:
        return (await self._session.exec(self._list(offset, limit))).all()

    async def find_by_id(self, id: UUID) -> T | None:
        return (await self._session.exec(self._get(id))).one_or_none()
    
    async def get_by_id(self, id: UUID) -> T:
        maybe_model = await self.find_by_id(id)
        if not maybe_model:
            raise HTTPException(status_code=404, detail=f"{self._table_model.__tablename__} {id} not found")
        return maybe_model
    
    async def delete_by_id(self, id: UUID) -> bool:
        model = await self.find_by_id(id)
        if not model:
            return False
        
        model.deleted = True
        await self._session.commit()
        return True