from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.schemas.email import DraftEmailRequest, EmailDraft
from app.services.email_draft import draft_email
from app.services.memory import get_history

router = APIRouter(prefix="/draft-email", tags=["email"])


@router.post("", response_model=EmailDraft)
def create_email_draft(request: DraftEmailRequest):
    history = get_history(request.session_id)
    if not history:
        raise HTTPException(status_code=404, detail="No conversation found for this session_id")

    try:
        return draft_email(history, request.tone)
    except ValidationError:
        raise HTTPException(status_code=502, detail="The model returned a draft in the wrong format. Please try again.")
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Could not get a draft from OpenAI: {error}")
