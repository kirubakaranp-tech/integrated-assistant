from collections import deque

from app.config import MEMORY_SIZE

sessions = {}


def get_history(session_id: str) -> list[dict]:
    return list(sessions.get(session_id, []))


def add_message(session_id: str, role: str, content: str):
    if session_id not in sessions:
        sessions[session_id] = deque(maxlen=MEMORY_SIZE)
    sessions[session_id].append({"role": role, "content": content})
