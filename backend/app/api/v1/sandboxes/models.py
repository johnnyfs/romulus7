from fastapi import Depends

from app.core.db import get_session
from app.core.models import TableBase
from app.core.repositories import Repository


class Sandbox(TableBase, table=True):
    __tablename__ = 'sandbox'
    name: str


class SandboxRepository(Repository[Sandbox]):
    def __init__(self, session = Depends(get_session)):
        super().__init__(table_model=Sandbox, session=session)
