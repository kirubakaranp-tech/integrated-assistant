import importlib

from fastapi.testclient import TestClient

from app import config
from app.main import app

client = TestClient(app)

PREFLIGHT_HEADERS = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}


def test_frontend_origin_is_allowed():
    response = client.options("/chat", headers={"Origin": "http://localhost:5500", **PREFLIGHT_HEADERS})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5500"


def test_other_websites_are_not_allowed():
    response = client.options("/chat", headers={"Origin": "https://evil.example.com", **PREFLIGHT_HEADERS})

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_not_every_origin_is_allowed():
    response = client.get("/health", headers={"Origin": "https://evil.example.com"})

    assert response.headers.get("access-control-allow-origin") != "*"


def test_spaces_in_allowed_origins_are_ignored(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5500, http://127.0.0.1:5500,")

    assert importlib.reload(config).ALLOWED_ORIGINS == ["http://localhost:5500", "http://127.0.0.1:5500"]
