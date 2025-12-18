from fastapi import FastAPI
from src.api import routes
from src.db.session import engine, Base

# Create Tables on Startup (The "Auto-Migration")
# In production, we would use Alembic, but this is Guerrilla Dev.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Glashaus API",
    description="Automated Real Estate Due Diligence Engine",
    version="0.1.0"
)

app.include_router(routes.router)

@app.get("/")
def health_check():
    return {
        "system": "GLASHAUS", 
        "status": "OPERATIONAL", 
        "motto": "Transparenz ist die Währung"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
