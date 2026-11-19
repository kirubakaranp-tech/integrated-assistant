from typing import Literal

from pydantic import BaseModel, Field


class DraftEmailRequest(BaseModel):
    session_id: str = Field(min_length=1, examples=["user-1"])
    tone: Literal["formal", "friendly"] = "formal"


class EmailDraft(BaseModel):
    subject: str = Field(min_length=1, examples=["Summary of your order query"])
    body: str = Field(min_length=1, examples=["Dear Rahul, ..."])
