import json

import requests
from fastapi.testclient import TestClient

from app.services import tools
from crm.main import app as crm_app

crm = TestClient(crm_app)


def use_mock_crm(monkeypatch):
    def fake_get(url, timeout):
        return crm.get(url.replace(tools.CRM_URL, ""))

    monkeypatch.setattr(tools.session, "get", fake_get)


def crm_fails_with(monkeypatch, error):
    def fake_get(url, timeout):
        raise error

    monkeypatch.setattr(tools.session, "get", fake_get)


def test_get_customer_details(monkeypatch):
    use_mock_crm(monkeypatch)

    result = tools.get_customer_details(3)

    customer = json.loads(result)
    assert customer["name"] == "Rahul"
    assert customer["plan"] == "Standard"


def test_unknown_customer(monkeypatch):
    use_mock_crm(monkeypatch)
    assert tools.get_customer_details(99) == "There is no customer with id 99."


def test_crm_timeout(monkeypatch):
    crm_fails_with(monkeypatch, requests.exceptions.ReadTimeout())
    assert tools.get_customer_details(3) == "The CRM did not answer in time. Please try again later."


def test_crm_down(monkeypatch):
    crm_fails_with(monkeypatch, requests.exceptions.ConnectionError())
    assert tools.get_customer_details(3) == "The CRM is not reachable right now. Please try again later."


def test_crm_server_errors_after_retries(monkeypatch):
    crm_fails_with(monkeypatch, requests.exceptions.RetryError())
    assert tools.get_customer_details(3) == "The CRM is having problems right now. Please try again later."


def test_session_retries_server_errors():
    retry = tools.session.get_adapter("http://").max_retries
    assert retry.total == 3
    assert 503 in retry.status_forcelist


def test_run_tool(monkeypatch):
    use_mock_crm(monkeypatch)

    assert "Rahul" in tools.run_tool("get_customer_details", {"customer_id": 3})
    assert tools.run_tool("delete_customer", {}) == "Unknown tool: delete_customer"
