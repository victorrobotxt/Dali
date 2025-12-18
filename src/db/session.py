from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

# Construct Database URL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"
)

# The Engine (The Connection to the Steel)
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# The Session Factory (Dispenses connections to requests)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The Base Class for all models
Base = declarative_base()

def get_db():
    """
    Dependency Injection for FastAPI.
    Opens a session, yields it, and ensures it closes even if logic crashes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
