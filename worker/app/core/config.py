from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BACKEND_ORIGIN: str
    BACKEND_PORT: int
    WORKER_ORIGIN: str
    WORKER_PORT: int
    WORKER_HEARTBEAT_SECONDS: float = 5.0

    @property
    def BACKEND_URL(self):
        return f"{self.BACKEND_ORIGIN}:{self.BACKEND_PORT}"

    @property
    def WORKER_URL(self):
        return f"{self.WORKER_ORIGIN}:{self.WORKER_PORT}"
    
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
