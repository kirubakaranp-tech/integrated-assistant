import json

import psycopg
import pytest

from app.config import DATABASE_URL
from app.services import order_tools
from app.services.tools import run_tool


@pytest.fixture
def database():
    try:
        psycopg.connect(DATABASE_URL, connect_timeout=3).close()
    except psycopg.OperationalError:
        pytest.skip("the orders database is not running")


def test_get_order_status(database):
    order = json.loads(order_tools.get_order_status(1042))

    assert order["status"] == "out_for_delivery"
    assert order["shipped_date"] == "2026-03-12"
    assert [item["product_name"] for item in order["items"]] == ["Wireless Earbuds", "USB-C Charger"]


def test_unknown_order(database):
    assert order_tools.get_order_status(9999) == "There is no order with id 9999."


def test_get_customer_orders(database):
    orders = json.loads(order_tools.get_customer_orders(3))

    assert [order["id"] for order in orders] == [1047, 1042, 1038, 1033]


def test_customer_without_orders(database):
    assert order_tools.get_customer_orders(42) == "Customer 42 has no orders."


def test_there_are_20_orders(database):
    with order_tools.connect() as conn:
        assert conn.execute("SELECT count(*) AS orders FROM orders").fetchone()["orders"] == 20


def test_assistant_user_cannot_change_data(database):
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        for sql in ["DELETE FROM orders", "UPDATE orders SET status = 'delivered'", "DROP TABLE orders"]:
            with pytest.raises(psycopg.Error):
                conn.execute(sql)


def test_no_rights_even_without_read_only_mode(database):
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute("SET default_transaction_read_only = off")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("DELETE FROM orders WHERE id = 1042")


def test_sql_in_the_id_is_refused():
    result = run_tool("get_order_status", {"order_id": "1042; DROP TABLE orders"})
    assert result == "Invalid arguments for get_order_status: the id must be a whole number."


def test_database_down_gives_a_clean_message(monkeypatch):
    monkeypatch.setattr(order_tools, "DATABASE_URL", "postgresql://nobody@127.0.0.1:1/none")

    assert order_tools.get_order_status(1042) == (
        "The order database is not reachable right now. Please try again later."
    )
