from common.core.config import BaseAppSettings


class Settings(BaseAppSettings):
    CHUNK_SIZE:    int = 3
    CHUNK_OVERLAP: int = 1


settings = Settings()