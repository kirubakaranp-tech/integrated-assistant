from fastapi.testclient import TestClient

from crm.main import app

crm = TestClient(app)


def test_get_customer():
    response = crm.get("/customers/3")

    assert response.status_code == 200
    assert response.json() == {
        "id": 3,
        "name": "Rahul",
        "plan": "Standard",
        "email": "rahul@example.com",
        "city": "Mumbai",
    }


def test_all_5_customers_exist():
    for customer_id in range(1, 6):
        assert crm.get(f"/customers/{customer_id}").status_code == 200


def test_unknown_customer_returns_404():
    assert crm.get("/customers/99").status_code == 404
