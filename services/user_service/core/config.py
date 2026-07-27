from common.core.config import BaseAppSettings

class Settings(BaseAppSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    OWNER_USERNAME: str = "owner"
    OWNER_PASSWORD: str = "123"


settings = Settings()