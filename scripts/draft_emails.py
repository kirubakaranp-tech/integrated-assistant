import requests

BASE_URL = "http://127.0.0.1:8000"

CONVERSATIONS = [
    {
        "session_id": "email-demo-1",
        "tone": "formal",
        "questions": ["Which plan is customer 3 on?", "Where is order 1042?"],
    },
    {
        "session_id": "email-demo-2",
        "tone": "friendly",
        "questions": ["How many days of sick leave do employees get?", "And how many days of earned leave?"],
    },
]

for conversation in CONVERSATIONS:
    print(f"===== Conversation {conversation['session_id']} =====")
    for question in conversation["questions"]:
        answer = requests.post(
            f"{BASE_URL}/chat", json={"message": question, "session_id": conversation["session_id"]}, timeout=60
        ).json()
        print(f"User: {question}")
        print(f"Assistant: {answer.get('answer', answer)}")

    draft = requests.post(
        f"{BASE_URL}/draft-email",
        json={"session_id": conversation["session_id"], "tone": conversation["tone"]},
        timeout=60,
    ).json()
    print(f"\n----- Email draft ({conversation['tone']}) -----")
    print(f"Subject: {draft.get('subject')}")
    print(draft.get("body", draft))
    print()
