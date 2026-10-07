# BEAR BOT — Render

## Что теперь используется

Главный файл — `bot.py`.

Mini App, API, Telegram Bot, SQLite и встроенные изображения работают из одного Python-сервиса. Внешние URL картинок для Mini App больше не нужны: 30 изображений встроены прямо в `bot.py` как Base64.

`server.mjs` для запуска Mini App больше не требуется.

## Render

Build Command:
```bash
pip install -r requirements.txt
```

Start Command:
```bash
python bot.py
```

## Environment Variables

```env
BOT_TOKEN=ТОКЕН_БОТА
OWNER_ID=TELEGRAM_ID_ВЛАДЕЛЬЦА
ADMIN_IDS=TELEGRAM_ID_ВЛАДЕЛЬЦА
WEBAPP_URL=https://YOUR-SERVICE.onrender.com
DATABASE_PATH=bearbot.sqlite3
PORT=10000
```

## Важно

- `WEBAPP_URL` должен указывать на тот же Render Web Service.
- Кнопка Mini App отправляется ботом через Telegram Web App и получает настоящий `initData`.
- Обычное открытие Render URL в браузере остаётся доступно как preview.
- Для проверки подписки на Telegram-канал бот должен иметь возможность получить `chat_member` для этого канала.
- Реферальная ссылка создаётся через `/start ref_<ID>` и сохраняет связь приглашённого пользователя.

## Игровая часть

В этой версии игровые экраны являются бесплатными визуальными механиками: апгрейд с выбором предметов, мины с выбором количества мин, замедленная ракетка с отдельной кнопкой «Забрать» и анимация кейса.

Telegram Stars не используются как ставка в играх и не превращаются в игровой баланс. Платёж Stars может использоваться только для фиксированной цифровой покупки.
