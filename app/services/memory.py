from collections import deque

from app.config import MEMORY_SIZE

# session_id -> the last messages of that conversation.
# It lives in memory, so it is cleared when the server restarts.
sessions = {}


def get_history(session_id: str) -> list[dict]:
    return list(sessions.get(session_id, []))


def add_message(session_id: str, role: str, content: str):
    if session_id not in sessions:
        # a deque with maxlen drops the oldest message by itself when it is full
        sessions[session_id] = deque(maxlen=MEMORY_SIZE)
    sessions[session_id].append({"role": role, "content": content})
