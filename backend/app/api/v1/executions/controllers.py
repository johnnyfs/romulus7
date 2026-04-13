from uuid import UUID

from fastapi import Depends

from app.api.v1.dispatches.models import DispatchRepository
from app.api.v1.events.controllers import DispatchesController
from app.api.v1.executions.models import ExecutionRepository


class ExecutionsController:
    def __init__(
        self,
        execution_repository: ExecutionRepository = Depends(ExecutionRepository),
        dispatch_repository: DispatchRepository = Depends(DispatchRepository),
        dispatches_controller: DispatchesController = Depends(DispatchesController),
    ):
        self._execution_repository = execution_repository
        self._dispatch_repository = dispatch_repository
        self._dispatches_controller = dispatches_controller

    async def delete(self, execution_id: UUID) -> bool:
        dispatches = await self._dispatch_repository.list_by_execution_id(execution_id)
        for dispatch in dispatches:
            await self._dispatches_controller.delete(dispatch.id)

        return await self._execution_repository.delete_by_id(execution_id)
