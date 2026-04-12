from fastapi import FastAPI

from app.api.v1.workspaces.routers import app as workspaces

app = FastAPI()
app.mount("/workspaces", workspaces)