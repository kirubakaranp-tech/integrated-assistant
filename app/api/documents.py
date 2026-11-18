import os

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import MAX_FILE_SIZE_MB
from app.schemas.documents import DocumentInfo, UploadResponse
from app.services.chunking import split_text
from app.services.embeddings import embed_texts
from app.services.extractors import read_docx, read_pdf
from app.services.vector_store import list_documents, save_document

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = [".pdf", ".docx"]


# This is a normal "def" and not "async def" on purpose: FastAPI runs it in a
# separate thread, so reading a big file does not block other requests.
@router.post("", status_code=201, response_model=UploadResponse)
def upload_document(file: UploadFile):
    file_name = file.filename or ""
    extension = os.path.splitext(file_name)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only PDF (.pdf) and Word (.docx) files are allowed")

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty")
    if len(data) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"The file is bigger than {MAX_FILE_SIZE_MB} MB")

    # check the first bytes too, so a renamed file (like photo.png -> photo.pdf) is rejected
    if extension == ".pdf" and not data.startswith(b"%PDF"):
        raise HTTPException(status_code=415, detail="This is not a real PDF file")
    if extension == ".docx" and not data.startswith(b"PK"):
        raise HTTPException(status_code=415, detail="This is not a real Word file")

    # 1. read the text
    try:
        if extension == ".pdf":
            pages = read_pdf(data)  # one text per page
        else:
            pages = [read_docx(data)]  # a Word file has no fixed pages
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Could not read the file. It may be damaged or password protected.",
        )

    # 2. split it into chunks, page by page, and remember the page of each chunk
    chunks = []
    page_numbers = []
    for page_number, page_text in enumerate(pages, start=1):
        for chunk in split_text(page_text):
            chunks.append(chunk)
            page_numbers.append(page_number if extension == ".pdf" else None)

    if not chunks:
        raise HTTPException(status_code=422, detail="No text found in the file. Scanned PDFs are not supported.")

    # 3. create the embeddings
    try:
        embeddings = embed_texts(chunks)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not load the embedding model. The first run needs internet to download it.",
        )

    # 4. save everything in Chroma
    doc_id = save_document(file_name, chunks, embeddings, page_numbers)
    return {"id": doc_id, "chunks": len(chunks)}


@router.get("", response_model=list[DocumentInfo])
def get_documents():
    return list_documents()
