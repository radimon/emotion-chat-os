import time
from collections import defaultdict

class SessionStore:
    """
    In-memory conversation store.
    Structure:
    user_id -> session_id -> messages[]
    """

    def __init__(self, max_turns: int = 20):
        self.store = defaultdict(lambda: defaultdict(list))
        self.max_turns = max_turns

    def add_user_message(self, user_id: str, session_id: str, content: str):
        self._append(user_id, session_id, "user", content)

    def add_assistant_message(self, user_id: str, session_id: str, content: str):
        self._append(user_id, session_id, "assistant", content)

    def get_history(self, user_id: str, session_id: str):
        return self.store[user_id][session_id]
    
    def _append(self, user_id, session_id, role, content):
        msgs = self.store[user_id][session_id]
        msgs.append({"role": role, "content": content})

        # 防止 content 爆炸
        if len(msgs) > self.max_turns * 2:
            self.store[user_id][session_id] = msgs[-self.max_turns * 2:]