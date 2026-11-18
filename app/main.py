from fastapi import FastAPI

from app.api import chat, documents

app = FastAPI(title="Integrated AI Assistant")
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
