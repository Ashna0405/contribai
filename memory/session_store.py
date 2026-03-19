import json
import os

SESSION_FILE = os.path.join(os.path.dirname(__file__), "../data/output.json")

class SessionStore:
    def __init__(self):
        self._store = {}
        os.makedirs(os.path.dirname(os.path.abspath(SESSION_FILE)), exist_ok=True)

    def set(self, key: str, value: dict):
        self._store[key] = value
        self._save_to_disk()

    def get(self, key: str) -> dict:
        return self._store.get(key, {})

    def get_all(self) -> dict:
        return self._store

    def clear(self):
        self._store = {}
        self._save_to_disk()

    def _save_to_disk(self):
        with open(SESSION_FILE, "w") as f:
            json.dump(self._store, f, indent=2)

    def summary(self) -> str:
        lines = []
        for key, value in self._store.items():
            lines.append(f"[{key.upper()}]\n{json.dumps(value, indent=2)}")
        return "\n\n".join(lines)

session = SessionStore()
