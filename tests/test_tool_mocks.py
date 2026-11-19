import json
from datetime import date
from decimal import Decimal

import psycopg
import pytest
import requests

from app.services import order_tools, tools


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


class FakeCrm:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        if self.error:
            raise self.error
        return self.response


def use_crm(monkeypatch, fake):
    monkeypatch.setattr(tools.session, "get", fake.get)
    return fake


def test_crm_tool_returns_the_customer(monkeypatch):
    customer = {"id": 3, "name": "Rahul", "plan": "Standard", "email": "rahul@example.com", "city": "Mumbai"}
    fake = use_crm(monkeypatch, FakeCrm(FakeResponse(200, customer)))

    result = tools.get_customer_details(3)

    assert json.loads(result) == customer
    assert fake.calls == [(f"{tools.CRM_URL}/customers/3", tools.CRM_TIMEOUT)]


def test_crm_tool_404(monkeypatch):
    use_crm(monkeypatch, FakeCrm(FakeResponse(404, {"detail": "Customer not found"})))
    assert tools.get_customer_details(9) == "There is no customer with id 9."


def test_crm_tool_other_error_status(monkeypatch):
    use_crm(monkeypatch, FakeCrm(FakeResponse(500)))
    assert tools.get_customer_details(3) == "The CRM returned an error (status 500)."


@pytest.mark.parametrize(
    "error, message",
    [
        (requests.exceptions.ConnectTimeout(), "The CRM did not answer in time. Please try again later."),
        (requests.exceptions.ReadTimeout(), "The CRM did not answer in time. Please try again later."),
        (requests.exceptions.RetryError(), "The CRM is having problems right now. Please try again later."),
        (requests.exceptions.ConnectionError(), "The CRM is not reachable right now. Please try again later."),
    ],
)
def test_crm_tool_errors_become_clean_messages(monkeypatch, error, message):
    use_crm(monkeypatch, FakeCrm(error=error))
    assert tools.get_customer_details(3) == message


class FakeConnection:
    def __init__(self, results=None, error=None):
        self.results = list(results or [])
        self.error = error
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        if self.error:
            raise self.error
        self.queries.append((sql, params))
        return self

    def fetchone(self):
        return self.results.pop(0)

    def fetchall(self):
        return self.results.pop(0)


def use_database(monkeypatch, fake):
    monkeypatch.setattr(order_tools, "connect", lambda: fake)
    return fake


ORDER_1042 = {
    "id": 1042,
    "customer_id": 3,
    "status": "out_for_delivery",
    "order_date": date(2026, 3, 10),
    "shipped_date": date(2026, 3, 12),
    "delivered_date": None,
    "total_amount": Decimal("3297.00"),
}
ITEMS_1042 = [
    {"product_name": "Wireless Earbuds", "quantity": 1, "unit_price": Decimal("2499.00")},
    {"product_name": "USB-C Charger", "quantity": 2, "unit_price": Decimal("399.00")},
]


def test_order_tool_returns_order_and_items(monkeypatch):
    fake = use_database(monkeypatch, FakeConnection([dict(ORDER_1042), ITEMS_1042]))

    order = json.loads(order_tools.get_order_status(1042))

    assert order["status"] == "out_for_delivery"
    assert order["shipped_date"] == "2026-03-12"
    assert order["total_amount"] == "3297.00"
    assert [item["product_name"] for item in order["items"]] == ["Wireless Earbuds", "USB-C Charger"]
    assert [params for _, params in fake.queries] == [(1042,), (1042,)]


def test_order_tool_uses_parameters_not_string_building(monkeypatch):
    fake = use_database(monkeypatch, FakeConnection([None]))

    order_tools.get_order_status(1042)

    sql, params = fake.queries[0]
    assert "%s" in sql
    assert "1042" not in sql
    assert params == (1042,)


def test_order_tool_unknown_order(monkeypatch):
    use_database(monkeypatch, FakeConnection([None]))
    assert order_tools.get_order_status(9999) == "There is no order with id 9999."


def test_customer_orders_tool(monkeypatch):
    rows = [
        {"id": 1047, "status": "processing", "order_date": date(2026, 3, 15), "total_amount": Decimal("4999.00")},
        {"id": 1042, "status": "out_for_delivery", "order_date": date(2026, 3, 10), "total_amount": Decimal("3297.00")},
    ]
    fake = use_database(monkeypatch, FakeConnection([rows]))

    orders = json.loads(order_tools.get_customer_orders(3))

    assert [order["id"] for order in orders] == [1047, 1042]
    assert fake.queries[0][1] == (3,)


def test_customer_orders_tool_no_orders(monkeypatch):
    use_database(monkeypatch, FakeConnection([[]]))
    assert order_tools.get_customer_orders(42) == "Customer 42 has no orders."


def test_order_tool_database_down(monkeypatch):
    use_database(monkeypatch, FakeConnection(error=psycopg.OperationalError("connection refused")))

    assert order_tools.get_order_status(1042) == order_tools.DATABASE_DOWN
    assert order_tools.get_customer_orders(3) == order_tools.DATABASE_DOWN


def test_order_tool_database_error(monkeypatch):
    use_database(monkeypatch, FakeConnection(error=psycopg.errors.InsufficientPrivilege("permission denied")))

    assert order_tools.get_order_status(1042) == order_tools.DATABASE_ERROR
    assert order_tools.get_customer_orders(3) == order_tools.DATABASE_ERROR


def test_connection_failure_before_query(monkeypatch):
    def broken_connect():
        raise psycopg.OperationalError("could not connect")

    monkeypatch.setattr(order_tools, "connect", broken_connect)
    assert order_tools.get_order_status(1042) == order_tools.DATABASE_DOWN
