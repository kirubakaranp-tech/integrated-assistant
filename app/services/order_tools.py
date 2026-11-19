import json

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL

DATABASE_DOWN = "The order database is not reachable right now. Please try again later."
DATABASE_ERROR = "Could not read the order database."


def connect() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL, connect_timeout=5, row_factory=dict_row)
    conn.read_only = True
    return conn


def get_order_status(order_id: int) -> str:
    try:
        with connect() as conn:
            order = conn.execute(
                "SELECT id, customer_id, status, order_date, shipped_date, delivered_date, total_amount "
                "FROM orders WHERE id = %s",
                (order_id,),
            ).fetchone()
            if order is None:
                return f"There is no order with id {order_id}."

            order["items"] = conn.execute(
                "SELECT product_name, quantity, unit_price FROM order_items WHERE order_id = %s ORDER BY id",
                (order_id,),
            ).fetchall()
    except psycopg.OperationalError:
        return DATABASE_DOWN
    except psycopg.Error:
        return DATABASE_ERROR

    return json.dumps(order, default=str)


def get_customer_orders(customer_id: int) -> str:
    try:
        with connect() as conn:
            orders = conn.execute(
                "SELECT id, status, order_date, total_amount FROM orders "
                "WHERE customer_id = %s ORDER BY order_date DESC",
                (customer_id,),
            ).fetchall()
    except psycopg.OperationalError:
        return DATABASE_DOWN
    except psycopg.Error:
        return DATABASE_ERROR

    if not orders:
        return f"Customer {customer_id} has no orders."
    return json.dumps(orders, default=str)
