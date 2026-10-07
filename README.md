# BEAR BOT — Telegram Bot + Mini App

## Render (один Web Service)

Этот вариант запускается одним Python-сервисом. **`bot.py` сам отдаёт Telegram Mini App по `/`**, поэтому отдельный Node-сервис для `server.mjs` не нужен.

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
python bot.py
```

### Environment Variables
```env
BOT_TOKEN=ТОКЕН_БОТА
OWNER_ID=ТВОЙ_TELEGRAM_ID
ADMIN_IDS=ТВОЙ_TELEGRAM_ID
WEBAPP_URL=https://ТВОЙ-СЕРВИС.onrender.com
DATABASE_PATH=bearbot.sqlite3
PORT=10000
```

`WEBAPP_URL` должен быть **точным HTTPS-адресом Render Web Service**. Именно его бот использует для кнопки `Открыть BEAR BOT`.

## Важно

Если открыть `https://...onrender.com` обычным Chrome/Safari, Telegram не передаст `initData`, потому что это не запуск Mini App из Telegram. Теперь страница не падает с `empty initData`: она показывает визуальный preview.

Для реального аккаунта, баланса, заданий и API нужно открывать Mini App через кнопку бота **Открыть BEAR BOT** в Telegram.

## Файлы

- `bot.py` — бот, FastAPI, SQLite, Telegram Stars и сам Mini App.
- `requirements.txt` — Python-зависимости.
- `server.mjs` — отдельная Node.js визуальная версия; для одного Render Web Service её запускать не требуется.
- `package.json` — нужен только если отдельно запускается `server.mjs`.

Не вставляй `BOT_TOKEN` в код или GitHub — только в Render Environment Variables.
