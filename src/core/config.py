import os
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Glashaus"
    VERSION: str = "0.1.0"
    
    # Secrets
    GEMINI_API_KEY: str = "mock-key"
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_SERVER: str = ""
    POSTGRES_DB: str = "glashaus"
    POSTGRES_PASSWORD: str = "postgres"
    
    # Queue
    REDIS_URL: str = "redis://redis:6379/0"

    @property
    def DATABASE_URL(self) -> str:
        if not self.POSTGRES_SERVER:
            return "sqlite:///./glashaus.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    @field_validator("GEMINI_API_KEY")
    def validate_api_key(cls, v):
        # Allow mock-key only if explicitly in DEV mode or testing
        env_mode = os.getenv("ENV", "DEV")
        if v == "mock-key" and env_mode == "PROD":
            raise ValueError("FATAL: GEMINI_API_KEY is missing in PRODUCTION environment.")
        
        if v == "mock-key":
            print("--- WARNING: GEMINI_API_KEY is not set. Using MOCK mode. ---")
        return v

    class Config:
        env_file = ".env"

settings = Settings()
