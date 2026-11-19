import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import CRM_TIMEOUT, CRM_URL
from app.services.order_tools import get_customer_orders, get_order_status


def make_session() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
        read=False,
    )
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


session = make_session()


def get_customer_details(customer_id: int) -> str:
    try:
        response = session.get(f"{CRM_URL}/customers/{customer_id}", timeout=CRM_TIMEOUT)
    except requests.exceptions.Timeout:
        return "The CRM did not answer in time. Please try again later."
    except requests.exceptions.RetryError:
        return "The CRM is having problems right now. Please try again later."
    except requests.exceptions.ConnectionError:
        return "The CRM is not reachable right now. Please try again later."

    if response.status_code == 404:
        return f"There is no customer with id {customer_id}."
    if response.status_code != 200:
        return f"The CRM returned an error (status {response.status_code})."

    return json.dumps(response.json())


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_details",
            "description": "Get a customer's name, plan, email and city from the CRM using the customer id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": "The id of the customer, for example 3"},
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Get the status, dates, total and items of one order using the order id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "The id of the order, for example 1042"},
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_orders",
            "description": "List all orders of a customer (id, status, date, total) using the customer id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": "The id of the customer, for example 3"},
                },
                "required": ["customer_id"],
            },
        },
    },
]

TOOL_SOURCES = {
    "get_customer_details": "CRM",
    "get_order_status": "Orders database",
    "get_customer_orders": "Orders database",
}


def run_tool(name: str, arguments: dict) -> str:
    try:
        if name == "get_customer_details":
            return get_customer_details(int(arguments["customer_id"]))
        if name == "get_order_status":
            return get_order_status(int(arguments["order_id"]))
        if name == "get_customer_orders":
            return get_customer_orders(int(arguments["customer_id"]))
    except (KeyError, ValueError, TypeError):
        return f"Invalid arguments for {name}: the id must be a whole number."
    return f"Unknown tool: {name}"
