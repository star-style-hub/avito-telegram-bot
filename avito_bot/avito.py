import time
from typing import Any, Dict, List, Optional

import requests

BASE_URL = "https://api.avito.ru"
CHAT_URL = "https://www.avito.ru/profile/messenger/channel/{chat_id}"


class AvitoError(Exception):
    pass


class AvitoClient:
    def __init__(self, client_id: str, client_secret: str,
                 user_id: Optional[str] = None, session=None, timeout: int = 20):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_id = user_id
        self.session = session or requests.Session()
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_expires = 0.0

    def _fetch_token(self) -> str:
        try:
            r = self.session.post(
                BASE_URL + "/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise AvitoError("Сетевая ошибка при получении токена Avito: %s" % type(e).__name__)
        if r.status_code != 200:
            raise AvitoError("Avito не выдал токен (HTTP %s): проверьте AVITO_CLIENT_ID/SECRET" % r.status_code)
        data = r.json()
        self._token = data["access_token"]
        self._token_expires = time.time() + int(data.get("expires_in", 3600)) - 60
        return self._token

    def _get_token(self) -> str:
        if not self._token or time.time() >= self._token_expires:
            return self._fetch_token()
        return self._token

    def _get(self, path: str, params: Optional[dict] = None) -> Dict[str, Any]:
        for attempt in range(2):
            try:
                r = self.session.get(
                    BASE_URL + path,
                    params=params,
                    headers={"Authorization": "Bearer " + self._get_token()},
                    timeout=self.timeout,
                )
            except requests.RequestException as e:
                raise AvitoError("Сетевая ошибка Avito API: %s" % type(e).__name__)
            if r.status_code == 401 and attempt == 0:
                self._token = None
                continue
            if r.status_code == 429:
                raise AvitoError("Avito API: превышен лимит запросов (429)")
            if r.status_code != 200:
                raise AvitoError("Avito API %s вернул HTTP %s" % (path, r.status_code))
            return r.json()
        raise AvitoError("Avito API: не удалось авторизоваться")

    def get_user_id(self) -> str:
        if not self.user_id:
            self.user_id = str(self._get("/core/v1/accounts/self")["id"])
        return self.user_id

    def get_unread_chats(self) -> List[Dict[str, Any]]:
        uid = self.get_user_id()
        data = self._get(
            "/messenger/v2/accounts/%s/chats" % uid,
            {"unread_only": "true", "limit": 100},
        )
        return data.get("chats", [])


def extract_incoming(chat: Dict[str, Any], my_user_id: str) -> Optional[Dict[str, str]]:
    """Возвращает данные входящего последнего сообщения чата или None."""
    last = chat.get("last_message") or {}
    if last.get("direction") != "in" or not last.get("id"):
        return None
    if str(last.get("author_id")) == str(my_user_id):
        return None
    name = "Неизвестный"
    for u in chat.get("users", []):
        if str(u.get("id")) != str(my_user_id) and u.get("name"):
            name = u["name"]
            break
    return {
        "chat_id": str(chat["id"]),
        "message_id": str(last["id"]),
        "name": name,
        "url": CHAT_URL.format(chat_id=chat["id"]),
    }
