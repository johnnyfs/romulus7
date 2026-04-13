from fastapi import FastAPI

from app.api.v1.health.routers import app as health
from app.api.v1.workers.routers import app as workers
from app.api.v1.workspaces.routers import app as workspaces

app = FastAPI()
app.mount("/health", health)
app.mount("/workers", workers)
app.mount("/workspaces", workspaces)
