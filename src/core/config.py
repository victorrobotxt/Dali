import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Glashaus"
    VERSION: str = "1.0.0-PROD"
    ENV: str = Field("DEV", description="DEV or PROD")
    
    # SECURITY: No defaults allowed. App must crash if these are missing.
    GEMINI_API_KEY: str = Field(..., min_length=10, description="Must be set in .env")
    
    # Database
    POSTGRES_USER: str = Field(..., min_length=1)
    POSTGRES_PASSWORD: str = Field(..., min_length=1)
    POSTGRES_SERVER: str = Field(..., min_length=1)
    POSTGRES_DB: str = "glashaus_db"
    
    REDIS_URL: str = Field(..., min_length=1)

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
