from types import SimpleNamespace

from openai.types.chat import ChatCompletion

from app.services import llm


def openai_reply(content=None, tool_calls=None):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return ChatCompletion.model_validate(
        {
            "id": "test",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-4o-mini",
            "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
        }
    )


class FakeOpenAI:
    def __init__(self, replies):
        self.replies = replies
        self.sent = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, model, messages, tools, temperature):
        self.sent.append(list(messages))
        return self.replies.pop(0)


def test_answer_without_tool(monkeypatch):
    fake = FakeOpenAI([openai_reply(content="Employees get 10 days of sick leave.")])
    monkeypatch.setattr(llm, "get_client", lambda: fake)

    answer, tools_used = llm.ask_llm([{"role": "user", "content": "Sick leave?"}])

    assert answer == "Employees get 10 days of sick leave."
    assert tools_used == []


def test_model_calls_the_crm_tool(monkeypatch):
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "get_customer_details", "arguments": '{"customer_id": 3}'},
    }
    fake = FakeOpenAI(
        [
            openai_reply(tool_calls=[tool_call]),
            openai_reply(content="Customer 3 (Rahul) is on the Standard plan."),
        ]
    )
    monkeypatch.setattr(llm, "get_client", lambda: fake)
    monkeypatch.setattr(llm, "run_tool", lambda name, arguments: '{"id": 3, "name": "Rahul", "plan": "Standard"}')

    answer, tools_used = llm.ask_llm([{"role": "user", "content": "Which plan is customer 3 on?"}])

    assert answer == "Customer 3 (Rahul) is on the Standard plan."
    assert tools_used == ["get_customer_details(3)"]

    last_message = fake.sent[1][-1]
    assert last_message["role"] == "tool"
    assert last_message["tool_call_id"] == "call_1"
    assert "Rahul" in last_message["content"]


def test_crm_error_message_goes_to_the_model(monkeypatch):
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "get_customer_details", "arguments": '{"customer_id": 99}'},
    }
    fake = FakeOpenAI([openai_reply(tool_calls=[tool_call]), openai_reply(content="There is no customer with id 99.")])
    monkeypatch.setattr(llm, "get_client", lambda: fake)
    monkeypatch.setattr(llm, "run_tool", lambda name, arguments: "There is no customer with id 99.")

    answer, tools_used = llm.ask_llm([{"role": "user", "content": "Plan of customer 99?"}])

    assert fake.sent[1][-1]["content"] == "There is no customer with id 99."
    assert answer == "There is no customer with id 99."


def test_invalid_tool_arguments_do_not_crash(monkeypatch):
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "get_order_status", "arguments": '{"order_id": 10'},
    }
    fake = FakeOpenAI([openai_reply(tool_calls=[tool_call]), openai_reply(content="Which order do you mean?")])
    monkeypatch.setattr(llm, "get_client", lambda: fake)

    answer, tools_used = llm.ask_llm([{"role": "user", "content": "Where is my order?"}])

    assert fake.sent[1][-1]["content"] == "Invalid arguments for get_order_status: the id must be a whole number."
    assert answer == "Which order do you mean?"
    assert tools_used == ["get_order_status()"]


def test_empty_answer_does_not_crash(monkeypatch):
    fake = FakeOpenAI([openai_reply(content=None)])
    monkeypatch.setattr(llm, "get_client", lambda: fake)

    answer, tools_used = llm.ask_llm([{"role": "user", "content": "x"}])

    assert answer == ""
    assert tools_used == []
