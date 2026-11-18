from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, examples=["How many days of sick leave do employees get?"])
    session_id: str = Field(min_length=1, examples=["user-1"])


class Source(BaseModel):
    file: str
    page: int | None = None  # Word files have no page numbers


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    session_id: str
