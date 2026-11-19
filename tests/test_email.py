import json
from pathlib import Path
from types import SimpleNamespace

from openai.types.chat import ChatCompletion

from app.services import email_draft

SAMPLES = Path(__file__).parent.parent / "samples"


class FakeOpenAI:
    def __init__(self, reply_text):
        self.reply_text = reply_text
        self.sent = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, model, messages, response_format, temperature):
        self.sent.append(messages)
        return ChatCompletion.model_validate(
            {
                "id": "test",
                "object": "chat.completion",
                "created": 0,
                "model": "gpt-4o-mini",
                "choices": [
                    {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": self.reply_text}}
                ],
            }
        )


def use_fake_openai(monkeypatch, reply):
    fake = FakeOpenAI(reply if isinstance(reply, str) else json.dumps(reply))
    monkeypatch.setattr(email_draft, "get_client", lambda: fake)
    return fake


def chat(client, message, session_id):
    return client.post("/chat", json={"message": message, "session_id": session_id})


def draft(client, session_id, tone="formal"):
    return client.post("/draft-email", json={"session_id": session_id, "tone": tone})


def test_draft_for_an_order_conversation(client, fake_llm, monkeypatch):
    fake_llm.answer = "Order 1042 was shipped on 12 March and is out for delivery."
    fake_llm.tools_used = ["get_order_status(1042)"]
    chat(client, "Where is order 1042?", "rahul")

    fake = use_fake_openai(
        monkeypatch,
        {
            "subject": "Summary of your order query",
            "body": "Dear Rahul,\n\n- Order 1042 was shipped on 12 March and is out for delivery.\n\n"
            "Next steps: you will receive it soon.\n\nKind regards,\nCustomer Support Team",
        },
    )

    response = draft(client, "rahul", tone="formal")

    assert response.status_code == 200
    assert response.json()["subject"] == "Summary of your order query"
    assert response.json()["body"].startswith("Dear Rahul,")

    prompt = fake.sent[0][-1]["content"]
    assert "user: Where is order 1042?" in prompt
    assert "assistant: Order 1042 was shipped on 12 March" in prompt
    assert "Formal" in prompt


def test_draft_for_a_policy_conversation_in_friendly_tone(client, fake_llm, monkeypatch):
    data = (SAMPLES / "policy.pdf").read_bytes()
    client.post("/documents", files={"file": ("policy.pdf", data)})
    chat(client, "How many days of sick leave do employees get?", "anna")
    chat(client, "And how many days of earned leave?", "anna")

    fake = use_fake_openai(
        monkeypatch,
        {
            "subject": "Your leave questions",
            "body": "Hi there,\n\n- 10 days of sick leave ...\n\nBest,\nCustomer Support Team",
        },
    )

    response = draft(client, "anna", tone="friendly")

    assert response.status_code == 200
    assert response.json() == {
        "subject": "Your leave questions",
        "body": "Hi there,\n\n- 10 days of sick leave ...\n\nBest,\nCustomer Support Team",
    }
    prompt = fake.sent[0][-1]["content"]
    assert "Friendly" in prompt
    assert "And how many days of earned leave?" in prompt


def test_the_model_is_told_it_cannot_send(client, fake_llm, monkeypatch):
    chat(client, "Where is order 1042?", "s1")
    fake = use_fake_openai(monkeypatch, {"subject": "Hi", "body": "Dear customer, ..."})

    draft(client, "s1")

    system_prompt = fake.sent[0][0]["content"]
    assert "You cannot send emails" in system_prompt


def test_unknown_session_returns_404(client):
    response = draft(client, "nobody")
    assert response.status_code == 404


def test_wrong_tone_is_rejected(client):
    response = draft(client, "s1", tone="angry")
    assert response.status_code == 422


def test_bad_json_from_the_model_returns_502(client, fake_llm, monkeypatch):
    chat(client, "Where is order 1042?", "s1")
    use_fake_openai(monkeypatch, {"title": "no subject or body here"})

    response = draft(client, "s1")

    assert response.status_code == 502


def test_draft_only_has_subject_and_body(client, fake_llm, monkeypatch):
    chat(client, "Where is order 1042?", "s1")
    use_fake_openai(monkeypatch, {"subject": "Hi", "body": "Dear customer, ...", "send": True})

    response = draft(client, "s1")

    assert set(response.json()) == {"subject", "body"}
