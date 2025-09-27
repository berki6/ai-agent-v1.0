import os
from typing import Optional, List


class Settings:
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")

    # Optional monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")

    # Environment settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    IS_DEVELOPMENT: bool = ENVIRONMENT == "development"


settings = Settings()
