from datetime import datetime, timezone

from fastapi import Depends
from sqlmodel import select
from sqlalchemy import DateTime
from sqlmodel import Field

from app.core.db import get_session
from app.core.models import TableBase
from app.core.repositories import Repository


class Worker(TableBase, table=True):
    __tablename__ = 'worker'
    url: str
    heartbeat_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class WorkerRepository(Repository[Worker]):
    def __init__(self, session = Depends(get_session)):
        super().__init__(table_model=Worker, session=session)

    async def find_first(self) -> Worker | None:
        statement = select(self._table_model).where(self._table_model.deleted == False).limit(1)  # noqa: E712
        return (await self._session.exec(statement)).first()

    async def heartbeat_by_id(self, id):
        model = await self.get_by_id(id)
        heartbeat_at = datetime.now(timezone.utc)
        model.heartbeat_at = heartbeat_at
        model.updated_at = heartbeat_at
        await self._session.commit()
        await self._session.refresh(model)
        return model
