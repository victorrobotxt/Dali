from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Glashaus"
    VERSION: str = "0.1.0"
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "glashaus"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Computed at runtime if not provided (fixes f-string bug)
    DATABASE_URL: Optional[str] = None

    # AI & External APIs
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.0-flash"
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    
    # Security
    # CRITICAL: No default value. Must be set in .env or environment.
    SECRET_KEY: str
    
    # Infra
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Helper to construct DB URL dynamically if missing
    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
