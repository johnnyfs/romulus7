from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.events.notify_bus import PgNotifyBus
from app.api.v1.events.routers import app as events_app
from app.api.v1.routers import app as api_v1
from app.core.config import settings
from app.core.db import dispose_engine, get_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    default_session_factory = get_session_factory()
    configured_session_factory = getattr(
        events_app.state,
        "event_session_factory",
        default_session_factory,
    )

    if configured_session_factory is default_session_factory:
        notify_bus = PgNotifyBus(
            dsn=settings.DATABASE_LISTEN_URL,
            channel=settings.EVENT_NOTIFY_CHANNEL,
        )
        await notify_bus.start()
        events_app.state.event_notify_bus = notify_bus
        events_app.state.event_session_factory = default_session_factory
    else:
        # Tests inject a non-Postgres session factory plus a local wake-up
        # bus. In that case we keep the injected resources instead of
        # opening a real LISTEN connection.
        notify_bus = events_app.state.event_notify_bus

    try:
        yield
    finally:
        await notify_bus.close()
        await dispose_engine()


app = FastAPI(title="romulus", lifespan=lifespan)
app.mount("/api/v1", api_v1)

def main():
    pass

if __name__ == "__main__":
    main()
