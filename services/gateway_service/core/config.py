from common.core.config import BaseAppSettings


class Settings(BaseAppSettings):
    USER_SERVICE_URL:     str = "http://user-service:8001"
    DOCUMENT_SERVICE_URL: str = "http://document-service:8002"
    SEARCH_SERVICE_URL:   str = "http://search-service:8003"


settings = Settings()