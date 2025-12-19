from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import routes

app = FastAPI(
    title="Glashaus API",
    description="Automated Real Estate Due Diligence Engine",
    version="1.0.0"
)

# Allow connections from Frontend/Dashboard
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

@app.get("/")
def health_check():
    return {
        "system": "GLASHAUS", 
        "status": "OPERATIONAL", 
        "version": "1.0.0-PROD"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
