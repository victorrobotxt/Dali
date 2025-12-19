from fastapi import FastAPI
from src.api import routes

# Note: Base.metadata.create_all removed. 
# We now strictly use Alembic for schema management.

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
