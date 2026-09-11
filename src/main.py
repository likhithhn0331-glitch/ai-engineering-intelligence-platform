from fastapi import FastAPI

from src.api.document_routes import router as document_router

app = FastAPI(title="AI Engineering Intelligence Platform")


@app.get("/")
async def root():
    return {
        "application": "AI Engineering Intelligence Platform",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(document_router)
