import os
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
SAMPLES = Path("samples")
RESULTS_FILE = Path("output") / "scenario_results.md"
PAUSE_SECONDS = 15

SCENARIOS = [
    {
        "id": "D1",
        "type": "Document",
        "question": "How many days of earned leave do full-time employees get?",
        "expect_any": ["18"],
        "expect_source": "policy.pdf",
    },
    {
        "id": "D2",
        "type": "Document",
        "question": "How many days a week can head-office staff work remotely?",
        "expect_any": ["two", "2"],
        "expect_source": "policy.pdf",
    },
    {
        "id": "D3",
        "type": "Document",
        "question": "How long must a password be?",
        "expect_any": ["14"],
        "expect_source": "handbook.docx",
    },
    {
        "id": "U1",
        "type": "Unanswerable",
        "question": "What is the capital of France?",
        "expect_i_dont_know": True,
    },
    {
        "id": "U2",
        "type": "Unanswerable",
        "question": "What is the company dress code?",
        "expect_i_dont_know": True,
    },
    {
        "id": "C1",
        "type": "CRM",
        "question": "Which plan is customer 3 on?",
        "expect_all": ["Rahul", "Standard"],
        "expect_tool": "get_customer_details",
    },
    {
        "id": "C2",
        "type": "CRM",
        "question": "What is the email address of customer 9?",
        "expect_any": ["no customer", "not found", "does not exist", "doesn't exist", "couldn't find", "could not find"],
        "expect_tool": "get_customer_details",
    },
    {
        "id": "O1",
        "type": "Order",
        "question": "Where is order 1042?",
        "expect_any": ["out for delivery", "out_for_delivery"],
        "expect_tool": "get_order_status",
    },
    {
        "id": "O2",
        "type": "Order",
        "question": "Show me all orders of customer 3.",
        "expect_all": ["1047", "1042", "1038", "1033"],
        "expect_tool": "get_customer_orders",
    },
    {
        "id": "E1",
        "type": "Email draft",
        "question": "Which plan is customer 3 on?",
        "tone": "formal",
        "expect_all": ["Rahul"],
    },
]


def upload_samples():
    names = [document["name"] for document in requests.get(f"{BASE_URL}/documents", timeout=30).json()]
    for file_name in ["policy.pdf", "handbook.docx"]:
        if file_name not in names:
            with open(SAMPLES / file_name, "rb") as file:
                response = requests.post(f"{BASE_URL}/documents", files={"file": (file_name, file)}, timeout=300)
            print(f"Uploaded {file_name}: {response.status_code}")


def ask(question, session_id):
    response = requests.post(
        f"{BASE_URL}/chat", json={"message": question, "session_id": session_id}, timeout=120
    )
    return response.status_code, response.json()


def check_text(text, scenario):
    lower = text.lower()
    problems = []
    if "expect_all" in scenario:
        missing = [word for word in scenario["expect_all"] if word.lower() not in lower]
        if missing:
            problems.append(f"missing {', '.join(missing)}")
    if "expect_any" in scenario and not any(word.lower() in lower for word in scenario["expect_any"]):
        problems.append(f"expected one of: {', '.join(scenario['expect_any'])}")
    return problems


def run_chat_scenario(scenario):
    status, data = ask(scenario["question"], f"scenario-{uuid.uuid4().hex[:8]}")
    if status != 200:
        return [f"HTTP {status}: {data.get('detail', data)}"], data, []

    answer = data["answer"]
    tools_used = data["tools_used"]
    problems = check_text(answer, scenario)

    if scenario.get("expect_i_dont_know") and answer != "I don't know":
        problems.append("expected \"I don't know\"")
    if "expect_tool" in scenario and not any(tool.startswith(scenario["expect_tool"]) for tool in tools_used):
        problems.append(f"expected tool {scenario['expect_tool']}")
    if "expect_source" in scenario:
        files = [source["file"] for source in data["sources"]]
        if scenario["expect_source"] not in files:
            problems.append(f"expected source {scenario['expect_source']}, got {files or 'none'}")

    return problems, answer, tools_used


def run_email_scenario(scenario):
    session_id = f"scenario-{uuid.uuid4().hex[:8]}"
    status, data = ask(scenario["question"], session_id)
    if status != 200:
        return [f"chat HTTP {status}: {data.get('detail', data)}"], data, []
    tools_used = data["tools_used"]

    response = requests.post(
        f"{BASE_URL}/draft-email", json={"session_id": session_id, "tone": scenario["tone"]}, timeout=120
    )
    draft = response.json()
    if response.status_code != 200:
        return [f"draft HTTP {response.status_code}: {draft.get('detail', draft)}"], draft, tools_used

    problems = check_text(draft["body"], scenario)
    if not draft["body"].startswith("Dear"):
        problems.append("formal email should start with \"Dear\"")
    return problems, f"Subject: {draft['subject']}", tools_used


def short(text, length=70):
    text = " ".join(str(text).split()).replace("|", "/")
    return text if len(text) <= length else text[: length - 3] + "..."


def main():
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"Model: {model}")
    try:
        upload_samples()
    except requests.ConnectionError:
        print(f"Cannot reach the API at {BASE_URL}. Start it first: uvicorn app.main:app --reload")
        return

    rows = []
    for number, scenario in enumerate(SCENARIOS):
        if number > 0:
            time.sleep(PAUSE_SECONDS)

        start = time.perf_counter()
        try:
            if scenario["type"] == "Email draft":
                problems, answer, tools_used = run_email_scenario(scenario)
            else:
                problems, answer, tools_used = run_chat_scenario(scenario)
        except requests.RequestException as error:
            problems, answer, tools_used = [f"request failed: {error}"], "", []
        seconds = time.perf_counter() - start

        result = "PASS" if not problems else "FAIL"
        rows.append([scenario["id"], scenario["type"], scenario["question"], result, f"{seconds:.1f}s",
                     ", ".join(tools_used) or "-", answer, "; ".join(problems) or "-"])
        print(f"{scenario['id']} {result} {seconds:.1f}s {short(answer)}")
        for problem in problems:
            print(f"   - {problem}")

    passed = sum(1 for row in rows if row[3] == "PASS")
    lines = [
        "# Scenario results",
        "",
        f"Run: {datetime.now():%Y-%m-%d %H:%M} | Model: `{model}` | Passed: {passed}/{len(rows)}",
        "",
        "| # | Type | Question | Result | Time | Tools used | Answer | Problems |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(short(cell) for cell in row) + " |")

    RESULTS_FILE.parent.mkdir(exist_ok=True)
    RESULTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nPassed {passed}/{len(rows)}. Table saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
