from pathlib import Path

from pydantic_settings import BaseSettings

_ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "biometrics.db"
    FIREBASE_PROJECT_ID: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:9000", "http://localhost:5173", "*"]

    model_config = {"env_prefix": "", "env_file": str(_ROOT_ENV), "extra": "ignore"}


settings = Settings()
