import json
import os
from typing import Dict


class StateStore:
    """Хранит id последнего обработанного сообщения по каждому чату."""

    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, str] = {}
        self.exists = os.path.exists(path)
        if self.exists:
            try:
                with open(path, encoding="utf-8") as f:
                    self.data = json.load(f)
            except (ValueError, OSError):
                self.data = {}

    def is_seen(self, chat_id: str, message_id: str) -> bool:
        return self.data.get(chat_id) == message_id

    def mark(self, chat_id: str, message_id: str) -> None:
        self.data[chat_id] = message_id
        self.save()

    def save(self) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False)
        os.replace(tmp, self.path)
        self.exists = True
