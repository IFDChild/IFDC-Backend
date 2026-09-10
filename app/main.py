from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine
from app.models.blog import Blog
from app.models.user import User
from app.models.volunteer import VolunteerApplication
from app.routers.auth import router as auth_router, seed_admin
from app.routers.blogs import router as blog_router
from app.routers.uploads import router as upload_router
from app.routers.volunteers import router as volunteer_router



Base.metadata.create_all(
    bind=engine
)

with SessionLocal() as db:
    seed_admin(db)


app = FastAPI(
    title="IFDC Blog API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5180",
        "http://localhost:5181"
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
app.include_router(auth_router)
app.include_router(volunteer_router)

@app.get("/")
def root():
    return {
        "message": "IFDC Blog API is running"
    }