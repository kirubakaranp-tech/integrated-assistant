from pathlib import Path

from app.services import memory

SAMPLES = Path(__file__).parent.parent / "samples"


def upload_policy(client):
    data = (SAMPLES / "policy.pdf").read_bytes()
    client.post("/documents", files={"file": ("policy.pdf", data)})


def ask(client, message, session_id="s1"):
    return client.post("/chat", json={"message": message, "session_id": session_id})


def test_answer_with_sources(client, fake_llm):
    upload_policy(client)

    response = ask(client, "How many days of sick leave do employees get?")

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Employees get 10 days of sick leave each year."
    assert body["session_id"] == "s1"
    assert len(body["sources"]) > 0
    for source in body["sources"]:
        assert source["file"] == "policy.pdf"
        assert isinstance(source["page"], int)


def test_prompt_contains_the_chunks_and_the_question(client, fake_llm):
    upload_policy(client)

    ask(client, "How many days of sick leave do employees get?")

    messages = fake_llm.calls[0]
    assert messages[0]["role"] == "system"
    assert "I don't know" in messages[0]["content"]
    last = messages[-1]["content"]
    assert "Context:" in last
    assert "[policy.pdf, page" in last
    assert last.endswith("Question: How many days of sick leave do employees get?")


def test_follow_up_question_gets_the_history(client, fake_llm):
    upload_policy(client)

    ask(client, "How many days of sick leave do employees get?")
    ask(client, "And how many days of earned leave?")

    messages = fake_llm.calls[1]
    assert {"role": "user", "content": "How many days of sick leave do employees get?"} in messages
    assert {"role": "assistant", "content": "Employees get 10 days of sick leave each year."} in messages


def test_sessions_are_separate(client, fake_llm):
    upload_policy(client)

    ask(client, "How many days of sick leave do employees get?", session_id="anna")
    ask(client, "How many days of earned leave?", session_id="ravi")

    roles = [m["role"] for m in fake_llm.calls[1]]
    assert roles == ["system", "user"]  # ravi's chat has no history from anna's


def test_only_the_last_5_messages_are_kept(client, fake_llm):
    upload_policy(client)

    for i in range(4):  # 4 questions + 4 answers = 8 messages
        ask(client, f"Question {i} about leave")

    history = memory.get_history("s1")
    assert len(history) == 5
    assert history[-1]["role"] == "assistant"
    assert history[0]["content"] == "Employees get 10 days of sick leave each year."


def test_i_dont_know_when_there_are_no_documents(client, fake_llm):
    response = ask(client, "How many days of sick leave do employees get?")

    assert response.json()["answer"] == "I don't know"
    assert response.json()["sources"] == []
    assert fake_llm.calls == []  # the model was not even asked


def test_i_dont_know_when_nothing_relevant_is_found(client, fake_llm):
    upload_policy(client)

    response = ask(client, "What is the capital of France?")

    assert response.json() == {"answer": "I don't know", "sources": [], "session_id": "s1"}
    assert fake_llm.calls == []


def test_i_dont_know_from_the_model_has_no_sources(client, fake_llm):
    upload_policy(client)
    fake_llm.answer = "I don't know."

    response = ask(client, "How many days of sick leave do employees get?")

    assert response.json()["answer"] == "I don't know"
    assert response.json()["sources"] == []


def test_empty_message_is_rejected(client):
    response = ask(client, "")
    assert response.status_code == 422


def test_missing_session_id_is_rejected(client):
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 422


def test_llm_error_returns_503(client, monkeypatch):
    upload_policy(client)

    def llm_down(messages):
        raise ConnectionError("no internet")

    monkeypatch.setattr("app.api.chat.ask_llm", llm_down)
    response = ask(client, "How many days of sick leave do employees get?")
    assert response.status_code == 503
