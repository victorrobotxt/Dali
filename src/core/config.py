from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Glashaus"
    VERSION: str = "0.1.0"
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "glashaus"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    # AI & External APIs
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.0-flash"  # <--- Updated to 3.0-flash
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "changethis_in_production"
    
    # Infra
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
