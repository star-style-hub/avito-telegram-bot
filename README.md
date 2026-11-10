# avito-telegram-bot

Telegram-бот: присылает уведомление о новых входящих сообщениях на Авито:

> Новое сообщение от пользователя 'Имя' на Авито, 'https://www.avito.ru/profile/messenger/channel/<chat_id>'

Работает через опрос [Avito Messenger API](https://www.avito.ru/developers/api-catalog)
(`GET /messenger/v2/accounts/{user_id}/chats?unread_only=true`), OAuth `client_credentials`.
Повторные уведомления после перезапуска исключены (последнее обработанное сообщение чата хранится в `state.json`).
При первом запуске существующие непрочитанные не рассылаются (включить: `NOTIFY_EXISTING_UNREAD=true`).

## Настройка
1. Получите Client ID / Client secret в личном кабинете Авито (раздел API для профессионалов); у приложения нужен доступ к Messenger API.
2. Создайте бота у [@BotFather](https://t.me/BotFather), получите токен; напишите боту `/start` и узнайте свой chat id (например через @userinfobot).
3. Создайте `.env`:
   ```
   cp .env.example .env
   ```
   и заполните `AVITO_CLIENT_ID`, `AVITO_CLIENT_SECRET`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. `.env` в git не попадает.

## Запуск
```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m avito_bot.main
```

## Тесты
```
python -m pytest
```

Ссылка на чат строится по шаблону `https://www.avito.ru/profile/messenger/channel/<chat_id>`; если Авито изменит формат, поправьте `CHAT_URL` в `avito_bot/avito.py`.
