import os
import tempfile

# Use a temporary database for the tests, so the real data folder is not touched.
# This must be set before the app is imported.
os.environ["CHROMA_DIR"] = tempfile.mkdtemp()

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import memory, vector_store

KEYWORDS = ["leave", "laptop", "password", "holiday", "remote"]


def fake_embed(texts):
    # The real model has to be downloaded, so the tests use a simple fake:
    # count a few keywords. Texts about the same topic get similar vectors.
    vectors = []
    for text in texts:
        counts = [text.lower().count(word) for word in KEYWORDS] + [0.1]
        length = sum(c * c for c in counts) ** 0.5
        vectors.append([c / length for c in counts])
    return vectors


class FakeLLM:
    """Stands in for OpenAI. It remembers what it was asked."""

    def __init__(self):
        self.calls = []
        self.answer = "Employees get 10 days of sick leave each year."

    def __call__(self, messages):
        self.calls.append(messages)
        return self.answer


@pytest.fixture
def fake_llm(monkeypatch):
    llm = FakeLLM()
    monkeypatch.setattr("app.api.chat.ask_llm", llm)
    return llm


@pytest.fixture
def client(monkeypatch, fake_llm):
    # start every test with an empty database and no chat history
    ids = vector_store.collection.get()["ids"]
    if ids:
        vector_store.collection.delete(ids=ids)
    memory.sessions.clear()

    monkeypatch.setattr("app.api.documents.embed_texts", fake_embed)
    monkeypatch.setattr("app.api.chat.embed_texts", fake_embed)
    return TestClient(app)
