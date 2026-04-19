from common.core.config import BaseAppSettings


class Settings(BaseAppSettings):
    DEF_TOP_K:     int   = 5
    DEF_MIN_SCORE: float = 0.4
    DEF_MIN_DIF:   float = 0.05


settings = Settings()