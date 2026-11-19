import requests

CHAT_URL = "http://127.0.0.1:8000/chat"

QUESTIONS = [
    "Where is order 1042?",
    "Which items are in that order?",
    "Show me all orders of customer 3.",
    "Has order 1035 been delivered?",
    "What is the status of order 9999?",
]

for question in QUESTIONS:
    response = requests.post(CHAT_URL, json={"message": question, "session_id": "demo"}, timeout=60)
    data = response.json()

    print(f"User: {question}")
    for tool in data.get("tools_used", []):
        print(f"Tool: {tool}")
    print(f"Assistant: {data.get('answer', data)}")
    print()
