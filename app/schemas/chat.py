from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, examples=["Which plan is customer 3 on?"])
    session_id: str = Field(min_length=1, examples=["user-1"])


class Source(BaseModel):
    file: str
    page: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    tools_used: list[str] = []
    session_id: str
