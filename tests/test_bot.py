import pytest

from avito_bot.avito import extract_incoming
from avito_bot.config import ConfigError, load_config
from avito_bot.main import poll_once
from avito_bot.state import StateStore
from avito_bot.telegram import TelegramError, format_message

ENV = {"AVITO_CLIENT_ID": "a", "AVITO_CLIENT_SECRET": "b",
       "TELEGRAM_BOT_TOKEN": "c", "TELEGRAM_CHAT_ID": "d"}


def chat(cid="c1", mid="m1", direction="in", author=2, content=None, mtype="text"):
    if content is None:
        content = {"text": "Привет, товар ещё продаётся?"}
    return {"id": cid,
            "users": [{"id": 1, "name": "Я"}, {"id": 2, "name": "Иван"}],
            "last_message": {"id": mid, "direction": direction, "author_id": author,
                             "type": mtype, "content": content}}


class FakeAvito:
    def __init__(self, chats):
        self.chats = chats

    def get_user_id(self):
        return "1"

    def get_unread_chats(self):
        return self.chats


class FakeTg:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def send(self, text):
        if self.fail:
            raise TelegramError("x")
        self.sent.append(text)


def test_config_validation():
    with pytest.raises(ConfigError):
        load_config({})
    assert load_config(ENV).poll_interval == 30
    with pytest.raises(ConfigError):
        load_config({**ENV, "POLL_INTERVAL_SECONDS": "abc"})


def test_message_format_and_extract():
    m = extract_incoming(chat(), "1")
    assert m["name"] == "Иван"
    assert m["text"] == "Привет, товар ещё продаётся?"
    assert format_message(m["name"], m["text"], m["url"], m["type"]) == (
        "Новое сообщение от 'Иван':\n\n"
        "'Привет, товар ещё продаётся?'\n\n"
        "'https://www.avito.ru/profile/messenger/channel/c1'")
    assert extract_incoming(chat(direction="out", author=1), "1") is None


@pytest.mark.parametrize("content", [{}, None, {"text": None}, {"image": {}}, "x"])
def test_non_text_message(content):
    c = chat(content=content if content is not None else {}, mtype="image")
    if content is None:
        c["last_message"].pop("content")
    m = extract_incoming(c, "1")
    assert m["text"] == ""
    out = format_message(m["name"], m["text"], m["url"], m["type"])
    assert "[сообщение без текста: image]" in out
    assert out.endswith("channel/c1'")


def test_long_text_truncated():
    out = format_message("Иван", "я" * 10000, "u")
    assert len(out) < 4096


def test_text_in_notification(tmp_path):
    tg = FakeTg()
    poll_once(FakeAvito([chat()]), tg, StateStore(str(tmp_path / "s.json")))
    assert "Привет, товар ещё продаётся?" in tg.sent[0]


def test_version():
    import avito_bot
    assert avito_bot.__version__ == "1.0.1"


def test_dedup_across_restart(tmp_path):
    path = str(tmp_path / "s.json")
    tg = FakeTg()
    assert poll_once(FakeAvito([chat()]), tg, StateStore(path)) == 1
    assert poll_once(FakeAvito([chat()]), tg, StateStore(path)) == 0
    assert poll_once(FakeAvito([chat(mid="m2")]), tg, StateStore(path)) == 1
    assert len(tg.sent) == 2


def test_baseline_no_spam(tmp_path):
    tg = FakeTg()
    st = StateStore(str(tmp_path / "s.json"))
    assert poll_once(FakeAvito([chat()]), tg, st, first_run_baseline=True) == 0
    assert poll_once(FakeAvito([chat()]), tg, st) == 0
    assert tg.sent == []


def test_telegram_failure_retries(tmp_path):
    st = StateStore(str(tmp_path / "s.json"))
    assert poll_once(FakeAvito([chat()]), FakeTg(fail=True), st) == 0
    tg = FakeTg()
    assert poll_once(FakeAvito([chat()]), tg, st) == 1
