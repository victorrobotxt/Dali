import os

class Settings:
    PROJECT_NAME: str = "Glashaus"
    VERSION: str = "0.1.0"
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "mock-key")

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "glashaus")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")

    # NEW: Redis Configuration for Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    @property
    def DATABASE_URL(self) -> str:
        if not self.POSTGRES_SERVER:
            return "sqlite:///./glashaus.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()

if settings.GEMINI_API_KEY == "mock-key":
    print("--- WARNING: GEMINI_API_KEY is not set. Using MOCK mode. ---")
