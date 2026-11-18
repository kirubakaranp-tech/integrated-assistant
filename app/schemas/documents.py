from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: str
    chunks: int


class DocumentInfo(BaseModel):
    id: str
    name: str
