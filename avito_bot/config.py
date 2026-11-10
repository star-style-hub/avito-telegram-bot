import os
from dataclasses import dataclass
from typing import Mapping, Optional


class ConfigError(Exception):
    pass


@dataclass
class Config:
    avito_client_id: str
    avito_client_secret: str
    avito_user_id: Optional[str]
    telegram_bot_token: str
    telegram_chat_id: str
    poll_interval: float
    state_file: str
    notify_existing_unread: bool


def load_dotenv(path: str = ".env") -> None:
    """Минимальный разбор .env; уже заданные переменные окружения не перезаписываются."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), value)


def load_config(env: Optional[Mapping[str, str]] = None) -> Config:
    env = os.environ if env is None else env
    required = [
        "AVITO_CLIENT_ID",
        "AVITO_CLIENT_SECRET",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    missing = [k for k in required if not env.get(k, "").strip()]
    if missing:
        raise ConfigError(
            "Не заданы обязательные параметры в .env: " + ", ".join(missing)
        )
    try:
        interval = float(env.get("POLL_INTERVAL_SECONDS", "30") or "30")
    except ValueError:
        raise ConfigError("POLL_INTERVAL_SECONDS должно быть числом")
    if interval < 5:
        raise ConfigError("POLL_INTERVAL_SECONDS должно быть не меньше 5")
    return Config(
        avito_client_id=env["AVITO_CLIENT_ID"].strip(),
        avito_client_secret=env["AVITO_CLIENT_SECRET"].strip(),
        avito_user_id=(env.get("AVITO_USER_ID") or "").strip() or None,
        telegram_bot_token=env["TELEGRAM_BOT_TOKEN"].strip(),
        telegram_chat_id=env["TELEGRAM_CHAT_ID"].strip(),
        poll_interval=interval,
        state_file=(env.get("STATE_FILE") or "state.json").strip(),
        notify_existing_unread=(env.get("NOTIFY_EXISTING_UNREAD") or "")
        .strip()
        .lower()
        in ("1", "true", "yes"),
    )
