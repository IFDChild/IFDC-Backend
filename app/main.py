import os
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.database import Base, SessionLocal, engine
from app.models.blog import Blog
from app.models.user import User
from app.models.volunteer import VolunteerApplication
from app.models.partner import PartnerInquiry
from app.models.resource import Resource
from app.models.contact import ContactMessage
from app.models.news import News
from app.models.donation import DonationInterest
from app.routers.auth import router as auth_router, seed_admin
from app.routers.blogs import router as blog_router
from app.routers.uploads import router as upload_router
from app.routers.volunteers import router as volunteer_router
from app.routers.partners import router as partner_router
from app.routers.resources import router as resource_router
from app.routers.contact import router as contact_router
from app.routers.news import router as news_router
from app.routers.donations import router as donation_router



Base.metadata.create_all(
    bind=engine
)

with SessionLocal() as db:
    seed_admin(db)


app = FastAPI(
    title="IFDC Blog API",
    version="1.0.0"
)


# Local dev origins always work; production sites are listed in ALLOWED_ORIGINS
# as a comma-separated list, e.g. "https://ifdchild.org,https://admin.ifdchild.org".
LOCAL_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5180",
    "http://localhost:5181"
]

ALLOWED_ORIGINS = LOCAL_ORIGINS + [
    origin.strip().rstrip("/")
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def seed_uploads():
    """Copy the images and PDFs shipped with the repo onto an empty volume.

    Railway starts with a blank volume, so on the first deploy the media that
    older blogs, news posts and reports point at would be missing. Files that
    already exist are never overwritten, so anything uploaded through the
    dashboard stays untouched.
    """
    seed_dir = os.getenv("UPLOAD_SEED_DIR", "uploads_seed")
    if not os.path.isdir(seed_dir) or os.path.abspath(seed_dir) == os.path.abspath(UPLOAD_DIR):
        return

    copied = 0
    for folder, _, files in os.walk(seed_dir):
        target_folder = os.path.join(UPLOAD_DIR, os.path.relpath(folder, seed_dir))
        os.makedirs(target_folder, exist_ok=True)
        for name in files:
            target = os.path.join(target_folder, name)
            if not os.path.exists(target):
                shutil.copy2(os.path.join(folder, name), target)
                copied += 1

    if copied:
        print(f"Seeded {copied} upload(s) into {UPLOAD_DIR}")


seed_uploads()

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)

app.include_router(blog_router)
app.include_router(upload_router)
app.include_router(auth_router)
app.include_router(volunteer_router)
app.include_router(partner_router)
app.include_router(resource_router)
app.include_router(contact_router)
app.include_router(news_router)
app.include_router(donation_router)

@app.get("/")
def root():
    return {
        "message": "IFDC Blog API is running"
    }


@app.get("/health")
def health():
    """Used by Railway's healthcheck."""
    return {"status": "ok"}