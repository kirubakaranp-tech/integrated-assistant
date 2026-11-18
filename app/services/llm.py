from openai import OpenAI

from app.config import OPENAI_MODEL


def ask_llm(messages: list[dict]) -> str:
    """Send the conversation to OpenAI and return the answer."""
    # The client reads OPENAI_API_KEY from the environment (our .env file).
    # It is created here and not at the top, so the app still starts without a key.
    client = OpenAI()
    response = client.chat.completions.create(model=OPENAI_MODEL, messages=messages, temperature=0)
    return response.choices[0].message.content.strip()
