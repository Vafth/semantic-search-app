from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class BaseAppSettings(BaseSettings):
    # Shared across user, document, search, gateway
    POSTGRES_URL: str = "postgresql+asyncpg://admin:password123@localhost:5432/project_db"
    SECRET_KEY:   str = "change-me"
    ALGORITHM:    str = "HS256"

    # Shared across document, search
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    MODEL_SERVICE_URL: str = "http://localhost:8000"

    COLLECTIONS: dict = {
        "small_model": {
            "collection":  "docs_small_r2",
            "vector_size": 384,
        },
        "normal_model": {
            "collection":  "docs_english_r2",
            "vector_size": 768,
        },
        "multilingual_model": {
            "collection":  "docs_multilingual",
            "vector_size": 768,
        },
    }

    model_config = SettingsConfigDict(
        env_file          = os.getenv("ENV_FILE", ".env"),
        env_file_encoding = "utf-8",
        case_sensitive    = True,
        extra             = "ignore",
    )