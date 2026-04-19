from common.core.config import BaseAppSettings


class Settings(BaseAppSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


settings = Settings()