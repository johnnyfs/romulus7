from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    ECHO_SQL: bool = False

    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20
    EVENT_NOTIFY_CHANNEL: str = "events_channel"
    EVENT_STREAM_BATCH_SIZE: int = 100
    EVENT_STREAM_KEEPALIVE_SECONDS: int = 15

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_LISTEN_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
