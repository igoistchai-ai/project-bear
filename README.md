# BEAR BOT

Проект состоит из:

- `bot.py` — основной Telegram-бот, FastAPI API, SQLite, Telegram Mini App API, Stars, задания, кейсы, игры.
- `server.mjs` — отдельная Node.js-версия визуального Web App; ВСЕ 30 сгенерированных изображений уже встроены в него как Base64.
- `requirements.txt` — Python-зависимости.
- `package.json` — запуск `server.mjs`, если нужен отдельный Node Web Service.
- `.env` — секреты.

## ВАЖНО ДЛЯ RENDER

Если нужен **один Web Service**, используй основной `bot.py`:

Build:
`pip install -r requirements.txt`

Start:
`python bot.py`

`server.mjs` в таком варианте не запускай отдельно — он является самостоятельной версией Web App/визуального сервера.

Если хочешь запускать именно Node Web App отдельно:

Build:
`npm install`

Start:
`node server.mjs`

Для Telegram Mini App в продакшене URL Web App должен указывать на публичный адрес сервиса, который реально обслуживает Mini App.

## Изображения

`server.mjs` содержит 30 PNG внутри Base64. Отдельные PNG-файлы для работы Web App не требуются.

## ENV

Секреты не помещай в код:

BOT_TOKEN=...
OWNER_ID=...
ADMIN_IDS=...
WEBAPP_URL=https://...
DATABASE_PATH=bearbot.sqlite3
PORT=10000
