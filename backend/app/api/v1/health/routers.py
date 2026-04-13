from fastapi import FastAPI

from app.api.v1.health.schemas import HealthResponse

app = FastAPI()


@app.get("/")
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
