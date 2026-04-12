from fastapi import Depends
from sqlalchemy import Index, text

from app.core.db import get_session
from app.core.models import TableBase
from app.core.repositories import Repository


class Workspace(TableBase, table=True):
    __tablename__ = 'workspace'
    name: str

    __table_args__ = (
        Index(
            'unique_workspace_name_not_deleted', 
            'name',
            unique=True, 
            postgresql_where=text("deleted IS FALSE")
        ),
    )

class WorkspaceRepository(Repository[Workspace]):
    def __init__(self, session = Depends(get_session)):
        super().__init__(table_model=Workspace, session=session)