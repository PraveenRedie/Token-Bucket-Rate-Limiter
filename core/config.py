# app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Rate Limiter Service"
    API_VERSION: str = "v1"
    DEBUG: bool = False
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Default rate limit settings
    DEFAULT_TOKENS: int = 100  # Default tokens per bucket
    DEFAULT_REFILL_RATE: float = 1.0  # Tokens added per second
    DEFAULT_TIME_WINDOW: int = 60  # Time window in seconds
    
    class Config:
        env_file = ".env"

settings = Settings()