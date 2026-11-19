import json
from functools import lru_cache

from openai import OpenAI

from app.config import OPENAI_MODEL
from app.services.tools import TOOLS, run_tool

MAX_TOOL_ROUNDS = 3


@lru_cache
def get_client() -> OpenAI:
    return OpenAI()


def ask_llm(messages: list[dict]) -> tuple[str, list[str]]:
    client = get_client()
    messages = list(messages)
    tools_used = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(model=OPENAI_MODEL, messages=messages, tools=TOOLS, temperature=0)
        message = response.choices[0].message

        if not message.tool_calls:
            return (message.content or "").strip(), tools_used

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tool_call.model_dump() for tool_call in message.tool_calls],
            }
        )
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
            result = run_tool(name, arguments)

            arguments_text = ", ".join(str(value) for value in arguments.values())
            tools_used.append(f"{name}({arguments_text})")
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})

    return "Sorry, I could not finish the answer.", tools_used
