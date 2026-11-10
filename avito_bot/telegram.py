import time

import requests


class TelegramError(Exception):
    pass


class TelegramClient:
    def __init__(self, token: str, chat_id: str, session=None, timeout: int = 20):
        self.token = token
        self.chat_id = chat_id
        self.session = session or requests.Session()
        self.timeout = timeout

    def send(self, text: str) -> None:
        url = "https://api.telegram.org/bot%s/sendMessage" % self.token
        for attempt in range(3):
            try:
                r = self.session.post(
                    url,
                    json={"chat_id": self.chat_id, "text": text,
                          "disable_web_page_preview": True},
                    timeout=self.timeout,
                )
            except requests.RequestException as e:
                # Исключение может содержать URL с токеном — не выводим его.
                raise TelegramError("Сетевая ошибка Telegram: %s" % type(e).__name__)
            if r.status_code == 429 and attempt < 2:
                try:
                    wait = int(r.json().get("parameters", {}).get("retry_after", 1))
                except ValueError:
                    wait = 1
                time.sleep(min(wait, 60))
                continue
            if r.status_code != 200:
                raise TelegramError("Telegram API вернул HTTP %s" % r.status_code)
            return
        raise TelegramError("Telegram API: превышен лимит запросов")


def format_message(name: str, url: str) -> str:
    return "Новое сообщение от пользователя '%s' на Авито, '%s'" % (name, url)
