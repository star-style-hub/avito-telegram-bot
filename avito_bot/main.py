import logging
import sys
import time

from .avito import AvitoClient, AvitoError, extract_incoming
from .config import ConfigError, load_config, load_dotenv
from .state import StateStore
from .telegram import TelegramClient, TelegramError, format_message

log = logging.getLogger("avito_bot")


def poll_once(avito, tg, state, first_run_baseline: bool = False) -> int:
    """Один цикл опроса. Возвращает число отправленных уведомлений."""
    my_id = avito.get_user_id()
    sent = 0
    for chat in avito.get_unread_chats():
        msg = extract_incoming(chat, my_id)
        if not msg or state.is_seen(msg["chat_id"], msg["message_id"]):
            continue
        if first_run_baseline:
            state.mark(msg["chat_id"], msg["message_id"])
            continue
        try:
            tg.send(format_message(msg["name"], msg["url"]))
        except TelegramError as e:
            log.error("Не удалось отправить уведомление: %s", e)
            continue  # не помечаем — повторим на следующем цикле
        state.mark(msg["chat_id"], msg["message_id"])
        sent += 1
    if first_run_baseline:
        state.save()
    return sent


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()
    try:
        cfg = load_config()
    except ConfigError as e:
        log.error("%s (см. .env.example)", e)
        return 2
    avito = AvitoClient(cfg.avito_client_id, cfg.avito_client_secret, cfg.avito_user_id)
    tg = TelegramClient(cfg.telegram_bot_token, cfg.telegram_chat_id)
    state = StateStore(cfg.state_file)
    baseline = not state.exists and not cfg.notify_existing_unread
    log.info("Бот запущен, интервал опроса %s с", cfg.poll_interval)
    while True:
        try:
            n = poll_once(avito, tg, state, first_run_baseline=baseline)
            baseline = False
            if n:
                log.info("Отправлено уведомлений: %d", n)
        except AvitoError as e:
            log.error("%s", e)
        except KeyboardInterrupt:
            return 0
        except Exception:
            log.exception("Непредвиденная ошибка")
        try:
            time.sleep(cfg.poll_interval)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    sys.exit(main())
