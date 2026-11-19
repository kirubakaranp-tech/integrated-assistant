from fastapi import FastAPI, HTTPException

app = FastAPI(title="Mock CRM")

CUSTOMERS = {
    1: {"id": 1, "name": "Priya", "plan": "Premium", "email": "priya@example.com", "city": "Chennai"},
    2: {"id": 2, "name": "Arjun", "plan": "Basic", "email": "arjun@example.com", "city": "Bengaluru"},
    3: {"id": 3, "name": "Rahul", "plan": "Standard", "email": "rahul@example.com", "city": "Mumbai"},
    4: {"id": 4, "name": "Anjali", "plan": "Premium", "email": "anjali@example.com", "city": "Kochi"},
    5: {"id": 5, "name": "Vikram", "plan": "Basic", "email": "vikram@example.com", "city": "Delhi"},
}


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    if customer_id not in CUSTOMERS:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CUSTOMERS[customer_id]
