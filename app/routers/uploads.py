import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles


router = APIRouter(
    prefix="/api/uploads",
    tags=["Uploads"]
)


UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp"
}


ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx"
}


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...)
):

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format"
        )

    contents = await file.read()

    # 5 MB limit
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image size must be less than 5MB"
        )

    filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    return {
        "filename": filename,
        "url": f"/uploads/{filename}"
    }


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...)
):
    """Used for volunteer CV attachments."""

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="CV must be a PDF, DOC or DOCX file"
        )

    contents = await file.read()

    # 5 MB limit
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 5MB"
        )

    filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    return {
        "filename": filename,
        "url": f"/uploads/{filename}"
    }