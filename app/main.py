from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, documents, email
from app.config import ALLOWED_ORIGINS

app = FastAPI(title="Integrated AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(email.router)


@app.get("/health")
def health():
    return {"status": "ok"}
