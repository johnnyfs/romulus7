from fastapi import FastAPI

from app.api.v1.dispatch.routers import app as dispatch
from app.api.v1.health.routers import app as health

app = FastAPI()
app.mount("/dispatch", dispatch)
app.mount("/health", health)
