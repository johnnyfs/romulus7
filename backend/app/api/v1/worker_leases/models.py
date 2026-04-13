from collections import defaultdict
from typing import Sequence
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import Index, text
from sqlmodel import Field, select

from app.api.v1.sandboxes.models import Sandbox
from app.core.db import get_session
from app.core.models import TableBase
from app.core.repositories import Repository


class WorkerLease(TableBase, table=True):
    __tablename__ = 'worker_lease'
    worker_id: UUID = Field(foreign_key="worker.id")
    sandbox_id: UUID = Field(foreign_key="sandbox.id")

    __table_args__ = (
        Index(
            'unique_worker_lease_worker_id_sandbox_id_not_deleted',
            'worker_id',
            'sandbox_id',
            unique=True,
            postgresql_where=text("deleted IS FALSE"),
            sqlite_where=text("deleted IS FALSE"),
        ),
        Index(
            'unique_worker_lease_sandbox_id_not_deleted',
            'sandbox_id',
            unique=True,
            postgresql_where=text("deleted IS FALSE"),
            sqlite_where=text("deleted IS FALSE"),
        ),
    )


class WorkerLeaseRepository(Repository[WorkerLease]):
    def __init__(self, session = Depends(get_session)):
        super().__init__(table_model=WorkerLease, session=session)

    async def find_by_worker_id_and_sandbox_id(
        self,
        worker_id: UUID,
        sandbox_id: UUID,
    ) -> WorkerLease | None:
        statement = self._select().where(
            self._table_model.worker_id == worker_id,
            self._table_model.sandbox_id == sandbox_id,
        )
        return (await self._session.exec(statement)).one_or_none()

    async def find_by_sandbox_id(
        self,
        sandbox_id: UUID,
    ) -> WorkerLease | None:
        statement = self._select().where(self._table_model.sandbox_id == sandbox_id)
        return (await self._session.exec(statement)).one_or_none()

    async def create_for_worker(
        self,
        worker_id: UUID,
        sandbox_id: UUID,
    ) -> WorkerLease:
        maybe_existing = await self.find_by_worker_id_and_sandbox_id(worker_id, sandbox_id)
        if maybe_existing:
            raise HTTPException(
                status_code=409,
                detail=f"worker {worker_id} already leased to sandbox {sandbox_id}",
            )

        maybe_existing_for_sandbox = await self.find_by_sandbox_id(sandbox_id)
        if maybe_existing_for_sandbox:
            raise HTTPException(
                status_code=409,
                detail=f"sandbox {sandbox_id} already has an active worker lease",
            )

        return await self.create(worker_id=worker_id, sandbox_id=sandbox_id)

    async def list_with_sandbox_names_by_worker_ids(
        self,
        worker_ids: Sequence[UUID],
    ) -> dict[UUID, list[tuple[WorkerLease, str]]]:
        if not worker_ids:
            return {}

        statement = (
            select(WorkerLease, Sandbox.name)
            .join(Sandbox, Sandbox.id == WorkerLease.sandbox_id)
            .where(
                WorkerLease.deleted == False,  # noqa: E712
                Sandbox.deleted == False,  # noqa: E712
                WorkerLease.worker_id.in_(worker_ids),
            )
        )
        rows = (await self._session.exec(statement)).all()

        grouped_rows: dict[UUID, list[tuple[WorkerLease, str]]] = defaultdict(list)
        for lease, sandbox_name in rows:
            grouped_rows[lease.worker_id].append((lease, sandbox_name))

        return grouped_rows

    async def list_worker_lease_ids_by_sandbox_ids(
        self,
        sandbox_ids: Sequence[UUID],
    ) -> dict[UUID, UUID]:
        if not sandbox_ids:
            return {}

        statement = self._select().where(self._table_model.sandbox_id.in_(sandbox_ids))
        models = (await self._session.exec(statement)).all()
        return {model.sandbox_id: model.id for model in models}
