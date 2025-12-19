import os
from pydantic_settings import BaseSettings
from pydantic import Field, RedisDsn, field_validator
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Glashaus"
    VERSION: str = "1.0.0-PROD"
    ENV: str = Field("DEV", description="DEV or PROD")
    
    # Secrets - No default values allowed in PROD
    # The app will crash if these are missing in production mode
    GEMINI_API_KEY: str = Field(..., min_length=1, description="Google Gemini API Key")
    
    # Database
    POSTGRES_USER: str = Field("postgres", min_length=1)
    POSTGRES_PASSWORD: str = Field("postgres", min_length=1)
    POSTGRES_SERVER: str = Field("localhost", min_length=1)
    POSTGRES_DB: str = "glashaus"
    
    REDIS_URL: str = Field("redis://redis:6379/0")

    @property
    def DATABASE_URL(self) -> str:
        # Fallback for local dev if server is empty
        if self.ENV == "DEV" and not self.POSTGRES_SERVER:
             return "sqlite:///./glashaus.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    @field_validator("GEMINI_API_KEY")
    def validate_api_key_prod(cls, v, info):
        # In PROD, we strictly forbid "mock-key"
        if info.data.get('ENV') == 'PROD' and (v == "mock-key" or not v):
            raise ValueError("FATAL: Cannot use mock keys in PRODUCTION environment.")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
