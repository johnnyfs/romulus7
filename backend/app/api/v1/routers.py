from fastapi import FastAPI

from app.api.v1.dispatches.routers import app as dispatches
from app.api.v1.events.routers import app as events
from app.api.v1.executions.routers import app as executions
from app.api.v1.health.routers import app as health
from app.api.v1.sandboxes.routers import app as sandboxes
from app.api.v1.workers.routers import app as workers
from app.api.v1.workspaces.routers import app as workspaces

app = FastAPI()
app.mount("/dispatches", dispatches)
app.mount("/events", events)
app.mount("/executions", executions)
app.mount("/health", health)
app.mount("/sandboxes", sandboxes)
app.mount("/workers", workers)
app.mount("/workspaces", workspaces)
