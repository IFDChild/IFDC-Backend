from fastapi import FastAPI

from app.database import Base, engine

from app.models.blog import Blog
from app.models.news import News


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="IFDC Website API",
    description="Backend API for IFDC website",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "IFDC Website API is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }