from fastapi import FastAPI
from src.api import routes

app = FastAPI(
    title="Glashaus API",
    description="Automated Real Estate Due Diligence Engine",
    version="0.1.0"
)

# Register Router
app.include_router(routes.router)

@app.get("/")
def health_check():
    return {"status": "operational", "system": "GLASHAUS"}

if __name__ == "__main__":
    import uvicorn
    # Hot reload enabled for dev
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
