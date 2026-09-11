import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles


router = APIRouter(
    prefix="/api/uploads",
    tags=["Uploads"]
)


UPLOAD_DIR = "uploads"

THUMB_DIR = os.path.join(UPLOAD_DIR, "thumbs")

os.makedirs(THUMB_DIR, exist_ok=True)


def make_pdf_thumbnail(pdf_path: str, stem: str, width: int = 600):
    """Render page 1 of a PDF to a JPEG cover. Returns its URL or None."""
    try:
        import pymupdf
    except ImportError:
        return None

    try:
        doc = pymupdf.open(pdf_path)
        if doc.page_count == 0:
            doc.close()
            return None

        page = doc[0]
        zoom = width / page.rect.width if page.rect.width else 1
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        name = f"{stem}.jpg"
        pix.save(os.path.join(THUMB_DIR, name), jpg_quality=80)
        doc.close()
        return f"/uploads/thumbs/{name}"
    except Exception:
        return None

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

    # 50 MB limit - illustrated guides and scanned books are large
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 50MB"
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

    thumbnail_url = (
        make_pdf_thumbnail(file_path, os.path.splitext(filename)[0])
        if extension == ".pdf" else None
    )

    return {
        "filename": filename,
        "original_name": file.filename,
        "size": len(contents),
        "url": f"/uploads/{filename}",
        "thumbnail_url": thumbnail_url
    }