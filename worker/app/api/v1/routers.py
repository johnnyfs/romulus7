from fastapi import FastAPI

from app.api.v1.health.routers import app as health

app = FastAPI()
app.mount("/health", health)
