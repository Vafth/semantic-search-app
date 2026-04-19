from common.core.config import BaseAppSettings


class Settings(BaseAppSettings):
    SMALL_MODEL_ID: str = "ibm-granite/granite-embedding-small-english-r2"
    NORMAL_MODEL_ID: str = "ibm-granite/granite-embedding-english-r2"
    MULTI_MODEL_ID:  str = "ibm-granite/granite-embedding-278m-multilingual"
    DEFAULT_BATCH_SIZE: int = 32


settings = Settings()