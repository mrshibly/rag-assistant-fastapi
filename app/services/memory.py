from collections import defaultdict

MAX_HISTORY = 20


class MemoryService:
    def __init__(self):
        self._store: dict[str, list[dict]] = defaultdict(list)

    def get_history(self, session_id: str) -> list[dict]:
        return self._store[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        history = self._store[session_id]
        history.append({"role": role, "content": content})
        if len(history) > MAX_HISTORY:
            self._store[session_id] = history[-MAX_HISTORY:]

    def clear(self, session_id: str):
        self._store.pop(session_id, None)


memory_service = MemoryService()
