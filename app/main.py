from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models.blog import Blog
from app.routers.blogs import router as blog_router
from app.routers.uploads import router as upload_router



Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="IFDC Blog API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

app.include_router(blog_router)
app.include_router(upload_router)

@app.get("/")
def root():
    return {
        "message": "IFDC Blog API is running"
    }