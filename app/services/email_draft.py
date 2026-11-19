from app.config import OPENAI_MODEL
from app.schemas.email import EmailDraft
from app.services.llm import get_client

TONES = {
    "formal": "Formal and polite. Start with 'Dear <name>,' and end with 'Kind regards,'.",
    "friendly": "Friendly and warm, but still professional. Start with 'Hi <name>,' and end with 'Best,'.",
}

SYSTEM_PROMPT = """You write email drafts that summarise a conversation between a customer and our support assistant.
You only write the draft. You cannot send emails.

Reply with JSON only, in exactly this form:
{"subject": "...", "body": "..."}

The body must have:
- a greeting with the customer's name if the conversation mentions it, otherwise "Dear customer"
- the key points of the conversation, as short bullet points
- the next steps for the customer
- a short polite closing, signed "Customer Support Team"

Use only facts from the conversation. Do not invent order numbers, dates or prices."""


def draft_email(history: list[dict], tone: str) -> EmailDraft:
    conversation = "\n".join(f"{message['role']}: {message['content']}" for message in history)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Tone: {TONES[tone]}\n\nConversation:\n{conversation}"},
    ]

    response = get_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    return EmailDraft.model_validate_json(response.choices[0].message.content)
