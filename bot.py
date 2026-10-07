# ============================================================
# BEAR BOT — Telegram Bot + Telegram Mini App
# Single-file deployment for GitHub + Render
#
# IMPORTANT:
# 2) Put secrets into Render Environment Variables, NOT this file.
# 3) Telegram Stars are used only for supported digital purchases/top-ups. Virtual games do not take Stars as a gambling stake.
# 4) Random case rewards are virtual items and are NOT cash-equivalent.
# 5) Check the laws/rules applicable to your country before enabling
#    paid random-reward mechanics for real users.
#
# Render:
#   Build Command: pip install -r requirements.txt
#   Start Command: python bot.py
#
# If you insist on one file, the requirements below are still needed
# on Render. You can also install them manually:
#   pip install aiogram fastapi uvicorn python-dotenv
# ============================================================

import asyncio
import hashlib
import hmac
import html
import json
import os
import random
import secrets
import sqlite3
import time
import urllib.parse
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    LabeledPrice,
    PreCheckoutQuery,
    Update,
)
import uvicorn

load_dotenv()

# ============================================================
# CONFIG — CHANGE LINKS ONLY
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)

# Optional: comma separated Telegram IDs
# Example: ADMIN_IDS=123456789,987654321
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = {
    int(x.strip()) for x in ADMIN_IDS_RAW.split(",")
    if x.strip().isdigit()
}

WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()
DATABASE = os.getenv("DATABASE_PATH", "bearbot.sqlite3")
PORT = int(os.getenv("PORT", "10000"))

# ---------- YOUR IMAGE LINKS ----------
# Replace the placeholder strings with your direct image URLs.
ASSETS = {
    # Main branding / rewards
    "logo": "PASTE_LOGO_IMAGE_URL_HERE",
    "bear": "PASTE_BEAR_IMAGE_URL_HERE",
    "heart": "PASTE_HEART_IMAGE_URL_HERE",
    "cake": "PASTE_CAKE_IMAGE_URL_HERE",
    "rocket": "PASTE_ROCKET_IMAGE_URL_HERE",
    "racket": "PASTE_RACKET_IMAGE_URL_HERE",
    "diamond": "PASTE_DIAMOND_IMAGE_URL_HERE",
    "flowers": "PASTE_FLOWERS_GIFT_IMAGE_URL_HERE",
    "gift": "PASTE_GIFT_IMAGE_URL_HERE",
    "coin": "PASTE_COIN_IMAGE_URL_HERE",
    "stars": "PASTE_STARS_IMAGE_URL_HERE",
    "star": "PASTE_STAR_IMAGE_URL_HERE",
    "crown": "PASTE_CROWN_IMAGE_URL_HERE",

    # Cases
    "case_noob": "PASTE_NOOB_CASE_IMAGE_URL_HERE",
    "case_cash": "PASTE_BIG_CASH_CASE_IMAGE_URL_HERE",
    "case_business": "PASTE_BUSSINES_CASE_IMAGE_URL_HERE",

    # Games
    "upgrade": "PASTE_UPGRADE_IMAGE_URL_HERE",
    "racket_game": "PASTE_RACKET_GAME_IMAGE_URL_HERE",
    "mines": "PASTE_MINES_GAME_IMAGE_URL_HERE",
    "mines_icon": "PASTE_MINES_ICON_IMAGE_URL_HERE",
    "upgrade_icon": "PASTE_UPGRADE_ICON_IMAGE_URL_HERE",
    "rocket_icon": "PASTE_ROCKET_ICON_IMAGE_URL_HERE",
    "coin_game": "PASTE_COIN_GAME_IMAGE_URL_HERE",
    "game_extra": "PASTE_EXTRA_GAME_IMAGE_URL_HERE",
    "wheel": "PASTE_WHEEL_IMAGE_URL_HERE",

    # Navigation / interface
    "avatar_default": "PASTE_AVATAR_DEFAULT_IMAGE_URL_HERE",
    "nav_home": "PASTE_NAV_HOME_IMAGE_URL_HERE",
    "nav_tasks": "PASTE_NAV_TASKS_IMAGE_URL_HERE",
    "nav_games": "PASTE_NAV_GAMES_IMAGE_URL_HERE",
    "nav_profile": "PASTE_NAV_PROFILE_IMAGE_URL_HERE",
    "settings": "PASTE_SETTINGS_IMAGE_URL_HERE",
    "back": "PASTE_BACK_IMAGE_URL_HERE",
    "menu": "PASTE_MENU_IMAGE_URL_HERE",
    "language": "PASTE_LANGUAGE_IMAGE_URL_HERE",
    "support": "PASTE_SUPPORT_IMAGE_URL_HERE",
    "logout": "PASTE_LOGOUT_IMAGE_URL_HERE",
    "referral": "PASTE_REFERRAL_IMAGE_URL_HERE",
    "task_done": "PASTE_TASK_DONE_IMAGE_URL_HERE",
    "history": "PASTE_HISTORY_IMAGE_URL_HERE",
    "notification": "PASTE_NOTIFICATION_IMAGE_URL_HERE",
    "verified": "PASTE_VERIFIED_IMAGE_URL_HERE",
    "vip": "PASTE_VIP_IMAGE_URL_HERE",
    "loading": "PASTE_LOADING_IMAGE_URL_HERE",
    "loading2": "PASTE_LOADING2_IMAGE_URL_HERE",
    "success": "PASTE_SUCCESS_IMAGE_URL_HERE",
    "error": "PASTE_ERROR_IMAGE_URL_HERE",
    "close": "PASTE_CLOSE_IMAGE_URL_HERE",

    # Decorative / UI surfaces
    "bg_card": "PASTE_BG_CARD_IMAGE_URL_HERE",
    "bg_panel": "PASTE_BG_PANEL_IMAGE_URL_HERE",
    "bg_popup": "PASTE_BG_POPUP_IMAGE_URL_HERE",
    "progress_bar": "PASTE_PROGRESS_BAR_IMAGE_URL_HERE",
    "button_buy": "PASTE_BUTTON_BUY_IMAGE_URL_HERE",
    "button_open": "PASTE_BUTTON_OPEN_IMAGE_URL_HERE",
    "button_collect": "PASTE_BUTTON_COLLECT_IMAGE_URL_HERE",

    # Result / state graphics
    "win_banner": "PASTE_WIN_BANNER_IMAGE_URL_HERE",
    "upgrade_result": "PASTE_UPGRADE_RESULT_IMAGE_URL_HERE",
    "rocket_result": "PASTE_ROCKET_RESULT_IMAGE_URL_HERE",
    "mines_result": "PASTE_MINES_RESULT_IMAGE_URL_HERE",
    "stars_topup": "PASTE_STARS_TOPUP_IMAGE_URL_HERE",
    "mystery": "PASTE_MYSTERY_GIFT_IMAGE_URL_HERE",
    "footer": "PASTE_FOOTER_IMAGE_URL_HERE",
    "mine": "PASTE_MINE_IMAGE_URL_HERE",
}

# Full image checklist. Every value above is intentionally a separate URL slot,
# so you can paste one direct image URL per generated asset later.
IMAGE_CHECKLIST = [
    "logo", "bear", "heart", "cake", "rocket", "racket", "diamond",
    "flowers", "gift", "coin", "stars", "star", "crown",
    "case_noob", "case_cash", "case_business",
    "upgrade", "racket_game", "mines", "mines_icon", "upgrade_icon",
    "rocket_icon", "coin_game", "game_extra", "wheel",
    "avatar_default", "nav_home", "nav_tasks", "nav_games", "nav_profile",
    "settings", "back", "menu", "language", "support", "logout",
    "referral", "task_done", "history", "notification", "verified", "vip",
    "loading", "loading2", "success", "error", "close",
    "bg_card", "bg_panel", "bg_popup", "progress_bar",
    "button_buy", "button_open", "button_collect",
    "win_banner", "upgrade_result", "rocket_result", "mines_result",
    "stars_topup", "mystery", "footer", "mine",
]

# ---------- YOUR SOUND LINKS ----------
# Replace with direct .mp3/.ogg URLs.
# Web App sounds are handled by server.mjs.
SOUNDS = {}

# Optional social links used by the default tasks.
DEFAULT_LINKS = {
    "channel": "PASTE_CHANNEL_LINK_HERE",
    "kick": "PASTE_KICK_LINK_HERE",
    "extra": "PASTE_EXTRA_TASK_LINK_HERE",
}

# ============================================================
# CASE CONFIG
# ============================================================

# Prices are INTERNAL COINS, not Stars.
CASES = {
    "noob": {
        "name": "Noob",
        "price": 300,
        "image": ASSETS["case_noob"],
        "rewards": [
            ("bear", "Мишка", 5.5),
            ("heart", "Сердечки", 14.5),
            ("cake", "Торт", 2.0),
            ("rocket", "Ракета", 1.5),
            ("racket", "Ракетка", 1.0),
            ("diamond", "Алмаз", 1.0),
            ("coins_100", "100 монет", 24.0),
            ("coins_150", "150 монет", 25.0),
            ("coins_200", "200 монет", 25.5),
        ],
    },
    "big_cash": {
        "name": "Big Cash",
        "price": 900,
        "image": ASSETS["case_cash"],
        "rewards": [
            ("bear", "Мишка", 6.0),
            ("heart", "Сердечки", 14.0),
            ("cake", "Торт", 2.0),
            ("rocket", "Ракета", 1.5),
            ("racket", "Ракетка", 1.0),
            ("diamond", "Алмаз", 1.0),
            ("coins_300", "300 монет", 20.0),
            ("coins_450", "450 монет", 24.0),
            ("coins_600", "600 монет", 30.5),
        ],
    },
    "business": {
        "name": "Bussines",
        "price": 1900,
        "image": ASSETS["case_business"],
        "rewards": [
            ("bear", "Мишка", 6.0),
            ("heart", "Сердечки", 13.0),
            ("cake", "Торт", 2.0),
            ("rocket", "Ракета", 1.5),
            ("racket", "Ракетка", 1.0),
            ("diamond", "Алмаз", 1.0),
            ("coins_700", "700 монет", 18.0),
            ("coins_900", "900 монет", 24.0),
            ("coins_1200", "1200 монет", 33.5),
        ],
    },
}

REWARD_IMAGES = {}

COIN_REWARDS = {
    "coins_100": 100,
    "coins_150": 150,
    "coins_200": 200,
    "coins_300": 300,
    "coins_450": 450,
    "coins_600": 600,
    "coins_700": 700,
    "coins_900": 900,
    "coins_1200": 1200,
}

# ============================================================
# DATABASE
# ============================================================

db = sqlite3.connect(DATABASE, check_same_thread=False)
db.row_factory = sqlite3.Row
db_lock = asyncio.Lock()

def db_exec(sql: str, params=()):
    cur = db.execute(sql, params)
    db.commit()
    return cur

def db_one(sql: str, params=()):
    return db.execute(sql, params).fetchone()

def db_all(sql: str, params=()):
    return db.execute(sql, params).fetchall()

def init_db():
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT DEFAULT '',
        first_name TEXT DEFAULT '',
        coins INTEGER NOT NULL DEFAULT 0,
        stars_spent INTEGER NOT NULL DEFAULT 0,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        url TEXT NOT NULL,
        reward INTEGER NOT NULL DEFAULT 50,
        type TEXT NOT NULL DEFAULT 'link',
        active INTEGER NOT NULL DEFAULT 1,
        created_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS task_claims (
        user_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        claimed_at INTEGER NOT NULL,
        PRIMARY KEY(user_id, task_id)
    );

    CREATE TABLE IF NOT EXISTS case_opens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        case_key TEXT NOT NULL,
        reward_key TEXT NOT NULL,
        reward_name TEXT NOT NULL,
        created_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        telegram_charge_id TEXT UNIQUE,
        payload TEXT NOT NULL,
        stars INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        kind TEXT NOT NULL,
        amount INTEGER NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        created_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        referrer_id INTEGER,
        created_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS mines_games (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        mines_count INTEGER NOT NULL,
        mine_cells TEXT NOT NULL,
        opened_cells TEXT NOT NULL,
        multiplier REAL NOT NULL DEFAULT 1.0,
        status TEXT NOT NULL DEFAULT "active",
        created_at INTEGER NOT NULL,
        ended_at INTEGER
    );
    """)
    db.commit()

    # Default tasks. Admin can edit/add more from the panel.
    if not db_one("SELECT id FROM tasks LIMIT 1"):
        now = int(time.time())
        defaults = [
            ("Подписка на канал", "Подпишись на канал", DEFAULT_LINKS["channel"], 50, "link"),
            ("Подписка на Kick", "Подпишись на канал Kick", DEFAULT_LINKS["kick"], 50, "link"),
            ("Дополнительное задание", "Открой страницу задания", DEFAULT_LINKS["extra"], 50, "link"),
        ]
        for t in defaults:
            db_exec(
                "INSERT INTO tasks(title,description,url,reward,type,active,created_at) VALUES(?,?,?,?,?,?,?)",
                (*t, 1, now)
            )

init_db()

# ============================================================
# HELPERS
# ============================================================

def now():
    return int(time.time())

def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ADMIN_IDS

def weighted_reward(case_key: str):
    rewards = CASES[case_key]["rewards"]
    r = random.uniform(0, sum(x[2] for x in rewards))
    acc = 0
    for key, name, chance in rewards:
        acc += chance
        if r <= acc:
            return key, name, chance
    return rewards[-1]

def upsert_user(user_id: int, username="", first_name=""):
    t = now()
    existing = db_one("SELECT id FROM users WHERE id=?", (user_id,))
    if existing:
        db_exec(
            "UPDATE users SET username=?, first_name=?, updated_at=? WHERE id=?",
            (username or "", first_name or "", t, user_id)
        )
    else:
        db_exec(
            "INSERT INTO users(id,username,first_name,coins,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (user_id, username or "", first_name or "", 0, t, t)
        )

def change_coins(user_id: int, amount: int, kind: str, description: str):
    db_exec("UPDATE users SET coins=coins+?, updated_at=? WHERE id=?",
            (amount, now(), user_id))
    db_exec(
        "INSERT INTO transactions(user_id,kind,amount,description,created_at) VALUES(?,?,?,?,?)",
        (user_id, kind, amount, description, now())
    )

def user_data(user_id: int):
    row = db_one("SELECT * FROM users WHERE id=?", (user_id,))
    if not row:
        return None
    return dict(row)

def public_user(user_id: int):
    u = user_data(user_id)
    if not u:
        return None
    return {
        "id": u["id"],
        "username": u["username"],
        "first_name": u["first_name"],
        "coins": u["coins"],
        "stars_spent": u["stars_spent"],
        "is_admin": is_admin(user_id),
    }

def make_invoice_payload(user_id: int, stars: int):
    return f"balance:{user_id}:{stars}:{secrets.token_hex(8)}"

def verify_telegram_init_data(init_data: str, bot_token: str):
    if not init_data:
        raise ValueError("empty initData")

    pairs = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("missing hash")

    auth_date = int(pairs.get("auth_date", "0"))
    if not auth_date or time.time() - auth_date > 86400:
        raise ValueError("expired initData")

    data_check_string = "\n".join(
        f"{k}={pairs[k]}" for k in sorted(pairs)
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    calculated = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise ValueError("invalid initData")

    tg_user = json.loads(pairs.get("user", "{}"))
    if not tg_user.get("id"):
        raise ValueError("missing Telegram user")

    return tg_user

def auth_user_from_request(request: Request):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    # Development fallback is intentionally NOT enabled.
    tg_user = verify_telegram_init_data(init_data, BOT_TOKEN)
    uid = int(tg_user["id"])
    upsert_user(
        uid,
        tg_user.get("username", ""),
        tg_user.get("first_name", "")
    )
    return tg_user

# ============================================================
# TELEGRAM BOT
# ============================================================

bot = Bot(BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    if not message.from_user:
        return

    upsert_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or ""
    )

    text = (
        "<b>BEAR BOT</b>\n\n"
        "Добро пожаловать.\n"
        "Открой Mini App через кнопку ниже."
    )

    if WEBAPP_URL:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="Открыть BEAR BOT",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )]
            ]
        )
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer(
            text + "\n\nWEBAPP_URL пока не установлен в ENV."
        )

@dp.message(Command("id"))
async def id_handler(message: Message):
    if message.from_user:
        await message.answer(f"Ваш Telegram ID: <code>{message.from_user.id}</code>")

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    # Never blindly accept malformed payloads.
    payload = query.invoice_payload or ""
    if not payload.startswith("balance:"):
        await query.answer(ok=False, error_message="Некорректный платёж.")
        return
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    if not payment or not message.from_user:
        return

    uid = message.from_user.id
    payload = payment.invoice_payload

    # Idempotency: do not credit the same Telegram charge twice.
    existing = db_one(
        "SELECT id FROM payments WHERE telegram_charge_id=?",
        (payment.telegram_payment_charge_id,)
    )
    if existing:
        return

    try:
        _, payload_uid, stars, _nonce = payload.split(":", 3)
        payload_uid = int(payload_uid)
        stars = int(stars)
    except Exception:
        return

    if payload_uid != uid:
        return

    # Example conversion. Change this to your own business model.
    # 1 Star -> 10 internal coins.
    coins = stars * 10

    db_exec(
        "INSERT INTO payments(user_id,telegram_charge_id,payload,stars,status,created_at) "
        "VALUES(?,?,?,?,?,?)",
        (
            uid,
            payment.telegram_payment_charge_id,
            payload,
            stars,
            "paid",
            now()
        )
    )

    db_exec(
        "UPDATE users SET coins=coins+?, stars_spent=stars_spent+?, updated_at=? WHERE id=?",
        (coins, stars, now(), uid)
    )

    db_exec(
        "INSERT INTO transactions(user_id,kind,amount,description,created_at) "
        "VALUES(?,?,?,?,?)",
        (uid, "stars_topup", coins, f"Пополнение за {stars} Stars", now())
    )

    await message.answer(
        f"Пополнение успешно.\n"
        f"⭐ Stars: {stars}\n"
        f"Баланс: +{coins} монет"
    )

# ============================================================
# FASTAPI
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not BOT_TOKEN:
        print("WARNING: BOT_TOKEN is empty. Telegram bot is disabled.")
        yield
        return

    task = asyncio.create_task(dp.start_polling(bot))
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await bot.session.close()

app = FastAPI(title="BEAR BOT", lifespan=lifespan)

# ============================================================
# MINI APP HTML/CSS/JS
# ============================================================

HTML_PAGE = r"""
<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport"
      content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#1698f5">
<title>BEAR BOT</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>

<style>
/* ==========================================================
   BEAR BOT — LARGE CSS UI
   Soft blue Telegram Mini App aesthetic
   ========================================================== */

:root{
  --blue:#1498f5;
  --blue2:#55b9ff;
  --blue3:#eaf6ff;
  --navy:#132235;
  --muted:#8c9baa;
  --bg:#f4f7fb;
  --card:#ffffff;
  --green:#55c88a;
  --purple:#8d55ef;
  --red:#ed5962;
  --shadow:0 10px 35px rgba(30,80,120,.09);
  --radius:28px;
  --radius2:20px;
}

*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0;background:var(--bg);color:var(--navy);
font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",Arial,sans-serif}
body{min-height:100vh;overflow-x:hidden}
button,input{font:inherit}
button{border:0;cursor:pointer}
img{max-width:100%;display:block}

#app{width:100%;max-width:620px;margin:auto;min-height:100vh;padding-bottom:105px}
.screen{display:none;padding:16px 15px 25px;animation:fade .18s ease}
.screen.active{display:block}

@keyframes fade{
  from{opacity:0;transform:translateY(6px)}
  to{opacity:1;transform:none}
}

.top{
  position:relative;
  padding:9px 3px 16px;
  display:flex;
  justify-content:space-between;
  align-items:center;
}
.brand{
  display:flex;
  gap:10px;
  align-items:center;
  font-size:27px;
  font-weight:900;
  letter-spacing:-1px;
}
.brand img{
  width:43px;height:43px;border-radius:15px;object-fit:cover;
  box-shadow:0 8px 20px rgba(20,152,245,.18)
}

.balance{
  display:flex;align-items:center;gap:6px;
  background:#fff;border-radius:25px;padding:7px 8px 7px 11px;
  box-shadow:0 8px 25px rgba(20,60,90,.08);
  font-weight:900
}
.coin{
  width:28px;height:28px;border-radius:50%;
  display:grid;place-items:center;
  background:linear-gradient(145deg,#fff,#eaf7ff);
  color:var(--blue);font-size:14px;font-weight:1000;
  border:2px solid #d5efff
}
.plus{
  width:29px;height:29px;border-radius:50%;
  background:var(--blue);color:#fff;font-size:20px;
  line-height:29px
}

.hero{
  position:relative;overflow:hidden;
  border-radius:31px;padding:22px;
  min-height:190px;
  background:
   radial-gradient(circle at 85% 15%,rgba(255,255,255,.45),transparent 30%),
   linear-gradient(135deg,#159cf5,#58c4ff);
  color:#fff;box-shadow:0 18px 45px rgba(20,152,245,.22);
}
.hero:after{
  content:"";position:absolute;right:-75px;bottom:-100px;
  width:260px;height:260px;border-radius:50%;
  background:rgba(255,255,255,.11)
}
.hero-title{font-size:28px;font-weight:950;letter-spacing:-1px}
.hero-sub{opacity:.86;margin-top:4px;font-size:14px}
.hero-balance{font-size:43px;font-weight:1000;margin-top:22px}
.hero-balance small{font-size:16px;font-weight:800;opacity:.9}
.hero-img{
  position:absolute;right:8px;bottom:-7px;width:170px;height:170px;
  object-fit:contain;filter:drop-shadow(0 15px 15px rgba(0,50,100,.15))
}

.section-title{
  display:flex;align-items:end;justify-content:space-between;
  margin:24px 3px 12px
}
.section-title h2{margin:0;font-size:23px;letter-spacing:-.5px}
.section-title button{background:none;color:var(--blue);font-weight:900}

.card{
  background:var(--card);border-radius:var(--radius);
  box-shadow:var(--shadow);border:1px solid rgba(20,70,100,.025)
}
.row-card{
  padding:14px;display:flex;align-items:center;gap:12px;
  margin-bottom:9px
}
.iconbox{
  width:52px;height:52px;border-radius:18px;
  display:grid;place-items:center;background:#edf7ff;
  flex:0 0 auto
}
.iconbox img{width:42px;height:42px;object-fit:contain}
.row-main{flex:1;min-width:0}
.row-title{font-weight:850;font-size:17px}
.row-sub{font-size:13px;color:var(--muted);margin-top:3px}
.reward{color:var(--blue);font-size:17px;font-weight:950;white-space:nowrap}

.cases{
  display:grid;grid-template-columns:repeat(3,1fr);gap:10px
}
.case{
  padding:10px;border-radius:23px;background:#fff;
  box-shadow:var(--shadow);text-align:center;
  transition:.16s transform,.16s box-shadow;
}
.case:active{transform:scale(.97)}
.case img{height:105px;width:100%;object-fit:contain}
.case-name{font-size:14px;font-weight:950;margin-top:4px}
.case-price{
  margin-top:7px;display:inline-flex;align-items:center;gap:4px;
  padding:6px 9px;border-radius:15px;background:#eaf6ff;
  color:var(--blue);font-weight:950;font-size:13px
}

.task-list{overflow:hidden}
.task-card{display:flex;align-items:center;padding:14px;border-bottom:1px solid #edf0f3}
.task-card:last-child{border-bottom:0}
.task-card .iconbox{width:50px;height:50px}
.task-content{flex:1}
.task-button{
  background:var(--blue);color:#fff;padding:10px 14px;
  border-radius:16px;font-weight:850
}
.task-button.done{background:#e8f7ef;color:#36aa70}

.banner{
  margin-top:13px;padding:17px 18px;border-radius:24px;
  background:linear-gradient(135deg,#e9f6ff,#fff);
  display:flex;align-items:center;gap:13px
}
.banner strong{font-size:16px}
.banner p{margin:4px 0 0;color:var(--muted);font-size:13px}

.nav{
  position:fixed;z-index:50;left:50%;bottom:12px;transform:translateX(-50%);
  width:min(590px,calc(100% - 18px));
  padding:8px 7px;
  background:rgba(255,255,255,.95);
  backdrop-filter:blur(18px);
  border-radius:30px;
  box-shadow:0 12px 40px rgba(20,50,80,.18);
  display:grid;grid-template-columns:repeat(4,1fr);
  border:1px solid rgba(20,80,120,.05)
}
.nav button{
  position:relative;background:none;color:#96a3b0;
  border-radius:22px;padding:8px 2px;font-weight:800;
  font-size:12px;display:flex;flex-direction:column;align-items:center;gap:3px
}
.nav button.active{background:#eaf6ff;color:var(--blue)}
.nav .nav-icon{font-size:24px;line-height:25px}
.badge{
  position:absolute;top:1px;right:25%;
  background:#ef5660;color:#fff;border-radius:99px;
  min-width:20px;height:20px;font-size:11px;
  display:none;place-items:center
}
.badge.show{display:grid}

.profile-head{
  padding:22px;text-align:center;
  background:linear-gradient(145deg,#e9d4ff,#fff);
  border-radius:30px
}
.avatar{
  width:92px;height:92px;border-radius:50%;
  margin:0 auto 12px;border:5px solid #fff;
  box-shadow:0 10px 30px rgba(0,0,0,.12);
  object-fit:cover;background:#dff1ff
}
.profile-name{font-size:24px;font-weight:950}
.profile-username{color:var(--muted);margin-top:3px}
.profile-coins{font-size:27px;font-weight:1000;margin-top:10px}

.action-grid{
  display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px
}
.action{
  padding:17px;background:#fff;border-radius:22px;box-shadow:var(--shadow);
  font-weight:900
}
.action.primary{background:var(--blue);color:#fff}
.action.green{background:var(--green);color:#fff}

.game{
  overflow:hidden;margin-bottom:14px;border-radius:28px;
  background:#fff;box-shadow:var(--shadow)
}
.game-img{width:100%;height:190px;object-fit:cover;background:#092}
.game-body{padding:16px}
.game-title{font-size:23px;font-weight:950}
.game-desc{color:var(--muted);font-size:14px;margin-top:5px}
.play{
  margin-top:14px;background:var(--green);color:#fff;
  padding:13px 18px;border-radius:17px;font-weight:950;width:100%
}


/* Premium game UI */
.game{border:1px solid #e7eef5;transition:transform .2s ease,box-shadow .2s ease}
.game:active{transform:scale(.985)}
.game-img{background:linear-gradient(145deg,#dff4ff,#eef8ff)}
.mines-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:16px 0}
.mine-cell{aspect-ratio:1;border:0;border-radius:16px;background:linear-gradient(145deg,#eef8ff,#d9edf9);font-size:20px;font-weight:1000;color:#1498f5;box-shadow:inset 0 -3px 0 rgba(20,80,120,.08);transition:.18s}
.mine-cell.open{background:#fff;transform:scale(.96)}
.mine-cell.mine{background:#ffe8ea;color:#e84c5a}
.multiplier-big{text-align:center;font-size:54px;font-weight:1000;color:#1498f5;margin:10px 0}
.prize-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:14px}
.prize-mini{background:#f6f9fc;border:1px solid #e9eff4;border-radius:18px;padding:12px;text-align:center}
.prize-mini img{width:54px;height:54px;object-fit:contain}
.racket-arena{height:230px;border-radius:25px;background:radial-gradient(circle at 50% 20%,#eaf8ff,#cfeeff 45%,#b5e0fa);position:relative;overflow:hidden;display:grid;place-items:center}
.racket-ball{width:28px;height:28px;border-radius:50%;background:#fff;box-shadow:0 5px 15px rgba(0,0,0,.16);position:absolute;animation:racketBall 1.1s ease-in-out infinite alternate}
.racket-icon{font-size:84px;transform:rotate(-25deg);animation:racketSwing .9s ease-in-out infinite alternate}
@keyframes racketBall{from{left:18%;top:30%}to{left:72%;top:63%}}
@keyframes racketSwing{from{transform:rotate(-35deg) translateY(5px)}to{transform:rotate(25deg) translateY(-5px)}}
.win-gift{text-align:center;padding:12px}.win-gift img{width:150px;height:150px;object-fit:contain;animation:giftPop .55s cubic-bezier(.2,1.4,.4,1)}
@keyframes giftPop{from{transform:scale(.3) rotate(-12deg);opacity:0}to{transform:scale(1) rotate(0);opacity:1}}

.modal{
  position:fixed;inset:0;z-index:100;background:rgba(8,24,38,.48);
  backdrop-filter:blur(8px);display:none;align-items:end;justify-content:center
}
.modal.show{display:flex}
.sheet{
  width:min(620px,100%);max-height:88vh;overflow:auto;
  background:#fff;border-radius:31px 31px 0 0;padding:20px
}
.sheet-head{display:flex;justify-content:space-between;align-items:center}
.close{
  width:38px;height:38px;border-radius:50%;background:#f0f3f6
}
.input{
  width:100%;padding:14px 15px;border-radius:17px;
  border:1px solid #e3e8ed;background:#f8fafc;outline:none;
  margin-top:8px
}
.input:focus{border-color:var(--blue);box-shadow:0 0 0 4px #eaf6ff}
.form-label{font-size:13px;color:var(--muted);font-weight:800;margin-top:14px}
.btn{
  width:100%;margin-top:14px;padding:15px;border-radius:18px;
  background:var(--blue);color:#fff;font-weight:950
}
.btn.secondary{background:#edf1f5;color:var(--navy)}
.btn.danger{background:#fff0f0;color:#df4c55}

.wheel-wrap{
  width:290px;height:290px;margin:15px auto 10px;position:relative
}
.wheel{
  width:100%;height:100%;border-radius:50%;
  border:9px solid #fff;
  box-shadow:0 15px 45px rgba(20,60,90,.18);
  background:conic-gradient(
    #ffcd58 0deg 45deg,#ff8ba7 45deg 90deg,
    #72c8ff 90deg 135deg,#9b83ff 135deg 180deg,
    #61d8a0 180deg 225deg,#ff9d69 225deg 270deg,
    #77b8ff 270deg 315deg,#f38ed5 315deg 360deg
  );
  transition:transform 2.7s cubic-bezier(.12,.72,.14,1)
}
.pointer{
  position:absolute;top:-5px;left:50%;transform:translateX(-50%);
  width:0;height:0;border-left:13px solid transparent;
  border-right:13px solid transparent;border-top:28px solid #132235;
  z-index:2
}
.center-wheel{
  position:absolute;inset:0;margin:auto;width:74px;height:74px;
  border-radius:50%;background:#fff;display:grid;place-items:center;
  box-shadow:0 7px 20px rgba(0,0,0,.13);font-weight:1000;color:var(--blue)
}

.result{
  text-align:center;padding:18px;background:#f5fbff;border-radius:25px
}
.result img{width:130px;height:130px;object-fit:contain;margin:auto}
.result-name{font-size:25px;font-weight:1000;margin-top:5px}
.result-chance{color:var(--muted);margin-top:4px}

.admin-card{
  background:#f8fbff;padding:16px;border-radius:22px;margin-bottom:12px
}
.admin-title{font-weight:950;font-size:18px}

.toast{
  position:fixed;z-index:200;left:50%;top:18px;transform:translate(-50%,-20px);
  opacity:0;pointer-events:none;background:#14283b;color:#fff;
  padding:13px 17px;border-radius:18px;font-weight:800;
  box-shadow:0 12px 35px rgba(0,0,0,.18);transition:.2s;
  width:max-content;max-width:90%
}
.toast.show{opacity:1;transform:translate(-50%,0)}

.loading{
  position:fixed;inset:0;z-index:300;background:#f5f8fb;
  display:grid;place-items:center
}
.spinner{
  width:45px;height:45px;border:4px solid #dceefa;
  border-top-color:var(--blue);border-radius:50%;
  animation:spin .7s linear infinite
}
@keyframes spin{to{transform:rotate(360deg)}}

.upgrade-box{
  padding:18px;border-radius:28px;background:#fff;box-shadow:var(--shadow)
}
.upgrade-items{display:grid;grid-template-columns:1fr 45px 1fr;align-items:center;gap:10px}
.up-item{
  text-align:center;background:#f5f9fc;padding:12px;border-radius:22px
}
.up-item img{width:105px;height:105px;object-fit:contain;margin:auto}
.up-item strong{display:block;font-size:15px}
.arrow-circle{
  width:45px;height:45px;border-radius:50%;background:var(--blue);
  color:#fff;display:grid;place-items:center;font-size:20px
}
.chance-bar{height:13px;background:#eaf0f4;border-radius:99px;overflow:hidden;margin-top:13px}
.chance-fill{height:100%;width:72%;background:linear-gradient(90deg,#53c88a,#14a2f5);border-radius:99px}

@media(max-width:390px){
  .cases{gap:6px}
  .case{padding:7px}
  .case img{height:85px}
  .hero-img{width:135px;height:135px}
  .hero-balance{font-size:35px}
}
</style>
</head>

<body>

<div id="loading" class="loading"><div class="spinner"></div></div>
<div id="toast" class="toast"></div>

<div id="app">

  <!-- HOME -->
  <section id="screen-home" class="screen active">
    <div class="top">
      <div class="brand">
        <img id="brandLogo" src="">
        <span>BEAR BOT</span>
      </div>
      <div class="balance">
        <div class="coin">M</div>
        <span id="topCoins">0</span>
        <button class="plus" onclick="openTopup()">+</button>
      </div>
    </div>

    <div class="hero">
      <div class="hero-title">Привет, <span id="heroName">друг</span></div>
      <div class="hero-sub">Твой баланс</div>
      <div class="hero-balance"><span id="heroCoins">0</span> <small>монет</small></div>
      <img id="heroImage" class="hero-img" src="">
    </div>

    <div class="section-title">
      <h2>Кейсы</h2>
      <button onclick="showScreen('cases')">Все</button>
    </div>
    <div id="caseGrid" class="cases"></div>

    <div class="section-title">
      <h2>Задания</h2>
      <button onclick="showScreen('tasks')">Все</button>
    </div>
    <div id="homeTasks" class="card task-list"></div>

    <div class="banner">
      <div class="iconbox"><span style="font-size:27px">★</span></div>
      <div>
        <strong>За каждое задание +50 монет</strong>
        <p>Выполняй задания и открывай новые кейсы.</p>
      </div>
    </div>
  </section>

  <!-- CASES -->
  <section id="screen-cases" class="screen">
    <div class="section-title"><h2>Кейсы</h2></div>
    <div id="caseGrid2" class="cases"></div>

    <div class="section-title"><h2>Последние открытия</h2></div>
    <div id="caseHistory" class="card"></div>
  </section>

  <!-- TASKS -->
  <section id="screen-tasks" class="screen">
    <div class="section-title"><h2>Задания</h2></div>
    <div id="tasksList" class="card task-list"></div>
  </section>

  <!-- GAMES -->
  <section id="screen-games" class="screen">
    <div class="section-title"><h2>Игры</h2></div>

    <div class="game">
      <img id="upgradeGameImg" class="game-img" src="">
      <div class="game-body">
        <div class="game-title">Апгрейд</div>
        <div class="game-desc">Выбери подарок и попробуй улучшить его с красивой анимацией.</div>
        <button class="play" onclick="openUpgrade()">Открыть апгрейд</button>
      </div>
    </div>

    <div class="game">
      <img id="minesGameImg" class="game-img" src="">
      <div class="game-body">
        <div class="game-title">Мины</div>
        <div class="game-desc">Открывай клетки, увеличивай множитель и забирай виртуальный приз.</div>
        <button class="play" onclick="openMines()">Играть</button>
      </div>
    </div>

    <div class="game">
      <img id="extraGameImg" class="game-img" src="">
      <div class="game-body">
        <div class="game-title">Ракетка</div>
        <div class="game-desc">Динамичная мини-игра с раундом, множителем и эффектным результатом.</div>
        <button class="play" onclick="openRacket()">Играть</button>
      </div>
    </div>
  </section>

  <!-- PROFILE -->
  <section id="screen-profile" class="screen">
    <div class="profile-head">
      <img id="avatar" class="avatar" src="">
      <div id="profileName" class="profile-name">Пользователь</div>
      <div id="profileUsername" class="profile-username">@username</div>
      <div class="profile-coins"><span id="profileCoins">0</span> M</div>
    </div>

    <div class="action-grid">
      <button class="action green" onclick="openTopup()">＋ Пополнить</button>
      <button class="action" onclick="showHistory()">История</button>
      <button class="action" onclick="openReferrals()">Рефералы</button>
      <button class="action" onclick="showToast('Вывод доступен только для разрешённых виртуальных механик.')">Вывести</button>
    </div>

    <div class="section-title"><h2>О аккаунте</h2></div>
    <div class="card" style="padding:17px">
      <div class="row-card" style="box-shadow:none;padding:7px 0">
        <div class="row-main"><div class="row-title">Telegram ID</div></div>
        <div id="telegramId" class="reward">—</div>
      </div>
      <div class="row-card" style="box-shadow:none;padding:7px 0">
        <div class="row-main"><div class="row-title">Stars пополнено</div></div>
        <div id="starsSpent" class="reward">0</div>
      </div>
    </div>

    <div id="adminArea"></div>
  </section>

</div>

<!-- NAV -->
<nav class="nav">
  <button id="nav-home" class="active" onclick="showScreen('home')">
    <span class="nav-icon">⌂</span><span>Главная</span>
  </button>
  <button id="nav-tasks" onclick="showScreen('tasks')">
    <span class="nav-icon">☷</span><span>Задания</span>
    <span id="taskBadge" class="badge">0</span>
  </button>
  <button id="nav-games" onclick="showScreen('games')">
    <span class="nav-icon">♢</span><span>Игры</span>
  </button>
  <button id="nav-profile" onclick="showScreen('profile')">
    <span class="nav-icon">○</span><span>Профиль</span>
  </button>
</nav>

<!-- GENERIC MODAL -->
<div id="modal" class="modal" onclick="if(event.target===this)closeModal()">
  <div id="sheet" class="sheet"></div>
</div>

<script>
const tg = window.Telegram?.WebApp;
if(tg){
  tg.ready();
  tg.expand();
  try{tg.setHeaderColor('#1498f5');tg.setBackgroundColor('#f4f7fb')}catch(e){}
}

const ASSETS = __ASSETS_JSON__;
const SOUNDS = __SOUNDS_JSON__;

let STATE = {
  user:null,
  tasks:[],
  cases:[],
  history:[],
  currentScreen:'home'
};

const $ = id => document.getElementById(id);

function headers(){
  return {
    'Content-Type':'application/json',
    'X-Telegram-Init-Data': tg?.initData || ''
  };
}

async function api(path, options={}){
  const res = await fetch(path, {
    ...options,
    headers:{...headers(), ...(options.headers||{})}
  });
  const data = await res.json().catch(()=>({}));
  if(!res.ok) throw new Error(data.detail || data.error || 'Ошибка');
  return data;
}

function toast(text){
  const el=$('toast');
  el.textContent=text;
  el.classList.add('show');
  clearTimeout(window.__toast);
  window.__toast=setTimeout(()=>el.classList.remove('show'),2400);
}

function playSound(name){
  const url=SOUNDS[name];
  if(!url || url.startsWith('PASTE_')) return;
  try{
    const a=new Audio(url);
    a.volume=.65;
    a.play().catch(()=>{});
  }catch(e){}
}

function closeModal(){
  $('modal').classList.remove('show');
  $('sheet').innerHTML='';
}

function modal(html){
  $('sheet').innerHTML=html;
  $('modal').classList.add('show');
}

function showScreen(name){
  STATE.currentScreen=name;
  document.querySelectorAll('.screen').forEach(x=>x.classList.remove('active'));
  $('screen-'+name).classList.add('active');
  document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));
  const nav=$('nav-'+name);
  if(nav)nav.classList.add('active');

  if(name==='home') renderHome();
  if(name==='cases') renderCases();
  if(name==='tasks') renderTasks();
  if(name==='profile') renderProfile();
  if(name==='games') renderGames();
  window.scrollTo({top:0,behavior:'smooth'});
}

function img(url, cls=''){
  return `<img class="${cls}" src="${escapeHtml(url)}" onerror="this.style.visibility='hidden'">`;
}

function escapeHtml(s){
  return String(s??'').replace(/[&<>"']/g,m=>({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'
  }[m]));
}

function renderUser(){
  const u=STATE.user;
  if(!u)return;
  $('topCoins').textContent=u.coins;
  $('heroCoins').textContent=u.coins;
  $('heroName').textContent=u.first_name || 'друг';
  $('profileCoins').textContent=u.coins;
  $('profileName').textContent=u.first_name || 'Пользователь';
  $('profileUsername').textContent=u.username ? '@'+u.username : 'Telegram';
  $('telegramId').textContent=u.id;
  $('starsSpent').textContent=u.stars_spent;
  $('brandLogo').src=ASSETS.logo;
  $('heroImage').src=ASSETS.bear;

  let photo = tg?.initDataUnsafe?.user?.photo_url || ASSETS.logo;
  $('avatar').src=photo;
}

function caseCard(c){
  return `
    <button class="case" onclick="openCaseConfirm('${escapeHtml(c.key)}')">
      ${img(c.image)}
      <div class="case-name">${escapeHtml(c.name)}</div>
      <div class="case-price">M ${c.price}</div>
    </button>`;
}

function renderCases(){
  $('caseGrid').innerHTML=STATE.cases.map(caseCard).join('');
  $('caseGrid2').innerHTML=STATE.cases.map(caseCard).join('');
  $('caseHistory').innerHTML = STATE.history.length ?
    STATE.history.map(h=>`
      <div class="row-card">
        <div class="iconbox">${img(h.image)}</div>
        <div class="row-main">
          <div class="row-title">${escapeHtml(h.reward_name)}</div>
          <div class="row-sub">${escapeHtml(h.case_name)}</div>
        </div>
      </div>`).join('') :
    `<div style="padding:22px;text-align:center;color:var(--muted)">Пока нет открытий</div>`;
}

function taskCard(t){
  const done=t.done;
  return `
    <div class="task-card">
      <div class="iconbox"><span style="font-size:25px">★</span></div>
      <div class="task-content">
        <div class="row-title">${escapeHtml(t.title)}</div>
        <div class="row-sub">${escapeHtml(t.description)}</div>
      </div>
      <button class="task-button ${done?'done':''}"
              onclick="claimTask(${t.id}, '${escapeHtml(t.url)}', ${t.reward}, ${done})">
        ${done?'✓':`+${t.reward}`}
      </button>
    </div>`;
}

function renderTasks(){
  $('tasksList').innerHTML=STATE.tasks.length
    ? STATE.tasks.map(taskCard).join('')
    : `<div style="padding:22px;text-align:center;color:var(--muted)">Заданий пока нет</div>`;
  $('homeTasks').innerHTML=STATE.tasks.slice(0,3).map(taskCard).join('');
  const left=STATE.tasks.filter(x=>!x.done).length;
  $('taskBadge').textContent=left;
  $('taskBadge').classList.toggle('show',left>0);
}

async function claimTask(id,url,reward,done){
  if(done)return;
  if(url && !url.startsWith('PASTE_')){
    try{tg?.openTelegramLink(url)}catch(e){window.open(url,'_blank')}
  }
  modal(`
    <div class="sheet-head"><h2>Проверка задания</h2>
      <button class="close" onclick="closeModal()">×</button></div>
    <p style="color:var(--muted)">После перехода выполни задание и нажми кнопку проверки.</p>
    <button class="btn" onclick="verifyTask(${id})">Проверить задание</button>
  `);
}

async function verifyTask(id){
  try{
    const data=await api('/api/tasks/'+id+'/claim',{method:'POST'});
    STATE.user=data.user;
    STATE.tasks=data.tasks;
    renderUser();renderTasks();
    closeModal();
    toast(`+${data.reward} монет`);
    playSound('win');
  }catch(e){toast(e.message)}
}

function openCaseConfirm(key){
  const c=STATE.cases.find(x=>x.key===key);
  if(!c)return;
  modal(`
    <div class="sheet-head">
      <h2>Открыть ${escapeHtml(c.name)}</h2>
      <button class="close" onclick="closeModal()">×</button>
    </div>
    ${img(c.image,'case-preview')}
    <p style="color:var(--muted)">Стоимость: <b>${c.price} M</b></p>
    <button class="btn" onclick="openCase('${key}')">Открыть кейс</button>
    <button class="btn secondary" onclick="showChances('${key}')">Показать шансы</button>
  `);
}

function showChances(key){
  const c=STATE.cases.find(x=>x.key===key);
  modal(`
    <div class="sheet-head"><h2>Шансы — ${escapeHtml(c.name)}</h2>
    <button class="close" onclick="closeModal()">×</button></div>
    ${c.rewards.map(r=>`
      <div class="row-card" style="box-shadow:none;border-bottom:1px solid #eef2f5">
        <div class="iconbox">${img(r.image)}</div>
        <div class="row-main"><div class="row-title">${escapeHtml(r.name)}</div></div>
        <div class="reward">${r.chance}%</div>
      </div>`).join('')}
  `);
}

async function openCase(key){
  try{
    closeModal();
    playSound('case_open');
    const data=await api('/api/cases/'+key+'/open',{method:'POST'});
    STATE.user=data.user;
    STATE.history.unshift(data.result);
    renderUser();
    renderCases();

    modal(`
      <div class="result">
        ${img(data.result.image)}
        <div class="result-name">${escapeHtml(data.result.reward_name)}</div>
        <div class="result-chance">Шанс: ${data.result.chance}%</div>
        <button class="btn" onclick="closeModal()">Забрать</button>
      </div>
    `);
    if(data.result.rare) playSound('win');
  }catch(e){
    toast(e.message);
  }
}

function openTopup(){
  modal(`
    <div class="sheet-head"><h2>Пополнить баланс</h2>
      <button class="close" onclick="closeModal()">×</button></div>
    <p style="color:var(--muted)">Пополнение выполняется через Telegram Stars.</p>
    <div class="action-grid">
      <button class="action primary" onclick="buyStars(10)">⭐ 10</button>
      <button class="action primary" onclick="buyStars(50)">⭐ 50</button>
      <button class="action primary" onclick="buyStars(100)">⭐ 100</button>
      <button class="action primary" onclick="buyStars(500)">⭐ 500</button>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-top:15px">
      После успешного платежа баланс начисляется сервером.
    </p>
  `);
}

async function buyStars(stars){
  try{
    const data=await api('/api/payments/invoice',{
      method:'POST',
      body:JSON.stringify({stars})
    });
    closeModal();
    if(tg?.openInvoice){
      tg.openInvoice(data.invoice_link,(status)=>{
        if(status==='paid'){
          setTimeout(load,1200);
          toast('Платёж принят');
        }else if(status==='cancelled'){
          toast('Платёж отменён');
        }
      });
    }else{
      window.open(data.invoice_link,'_blank');
    }
  }catch(e){toast(e.message)}
}

function openCoinGame(){
  modal(`
    <div class="sheet-head"><h2>Монетка</h2>
    <button class="close" onclick="closeModal()">×</button></div>
    <div style="text-align:center;padding:10px">
      <div style="font-size:100px">◉</div>
      <p style="color:var(--muted)">Выбери сторону. Игра использует виртуальные монеты.</p>
      <div class="action-grid">
        <button class="action primary" onclick="flipCoin('heads')">Орел</button>
        <button class="action" onclick="flipCoin('tails')">Решка</button>
      </div>
    </div>
  `);
}

async function flipCoin(side){
  try{
    const d=await api('/api/games/coin',{
      method:'POST',body:JSON.stringify({side})
    });
    STATE.user=d.user;renderUser();
    playSound(d.win?'win':'coin');
    modal(`
      <div class="result">
        <div style="font-size:95px">${d.result==='heads'?'◉':'◌'}</div>
        <div class="result-name">${d.result==='heads'?'Орел':'Решка'}</div>
        <div class="result-chance">${d.win?'Победа +100 M':'Попробуй ещё раз'}</div>
        <button class="btn" onclick="closeModal()">Закрыть</button>
      </div>
    `);
  }catch(e){toast(e.message)}
}

function openUpgrade(){
  modal(`
    <div class="sheet-head"><h2>Апгрейд</h2>
    <button class="close" onclick="closeModal()">×</button></div>
    <div class="upgrade-box">
      <div class="upgrade-items">
        <div class="up-item">${img(ASSETS.heart)}<strong>Сердечки</strong></div>
        <div class="arrow-circle">→</div>
        <div class="up-item">${img(ASSETS.bear)}<strong>Мишка</strong></div>
      </div>
      <div style="text-align:center;margin-top:15px;font-weight:950">Шанс 72%</div>
      <div class="chance-bar"><div class="chance-fill"></div></div>
      <button class="btn" onclick="upgrade()">Запустить рулетку</button>
    </div>
  `);
}

async function upgrade(){
  try{
    playSound('upgrade');
    const d=await api('/api/games/upgrade',{method:'POST'});
    const wheel=document.querySelector('.wheel');
    if(wheel){
      wheel.style.transform=`rotate(${d.degrees}deg)`;
    }
    setTimeout(()=>{
      STATE.user=d.user;renderUser();
      toast(d.win?'Апгрейд успешен':'Не повезло');
    },1200);
  }catch(e){toast(e.message)}
}

function openWheel(){
  modal(`
    <div class="sheet-head"><h2>Колесо</h2>
    <button class="close" onclick="closeModal()">×</button></div>
    <div class="wheel-wrap">
      <div class="pointer"></div>
      <div class="wheel"></div>
      <div class="center-wheel">BEAR</div>
    </div>
    <button class="btn" onclick="spinWheel()">Крутить</button>
  `);
}

async function spinWheel(){
  try{
    const d=await api('/api/games/wheel',{method:'POST'});
    const wheel=document.querySelector('.wheel');
    if(wheel)wheel.style.transform=`rotate(${d.degrees}deg)`;
    setTimeout(()=>{
      STATE.user=d.user;renderUser();
      toast(`${d.reward>0?'+':''}${d.reward} M`);
      playSound(d.reward>0?'win':'click');
    },2600);
  }catch(e){toast(e.message)}
}


function openRacket(){
  modal(`
    <div class="sheet-head"><h2>Ракетка</h2><button class="close" onclick="closeModal()">×</button></div>
    <div class="racket-arena"><div class="racket-ball"></div><div class="racket-icon">🏓</div></div>
    <div class="multiplier-big" id="racketX">1.00x</div>
    <p style="text-align:center;color:var(--muted)">Раунд использует виртуальные игровые очки. Нажми старт и забери результат.</p>
    <button class="btn" id="racketBtn" onclick="playRacket()">Начать раунд</button>
  `);
}
async function playRacket(){
  const btn=document.querySelector('#racketBtn'); if(btn)btn.disabled=true;
  playSound('click');
  let x=1; const out=document.querySelector('#racketX');
  const timer=setInterval(()=>{x+=0.04; if(out)out.textContent=x.toFixed(2)+'x';},45);
  try{
    const d=await api('/api/games/racket',{method:'POST'});
    setTimeout(()=>{clearInterval(timer); if(out)out.textContent=d.multiplier.toFixed(2)+'x'; STATE.user=d.user;renderUser(); playSound(d.win?'gift_win':'mine'); toast(d.win?'Раунд завершён — приз начислен':'Раунд завершён'); if(btn)btn.disabled=false;},700);
  }catch(e){clearInterval(timer); if(btn)btn.disabled=false; toast(e.message)}
}

function openMines(){
  modal(`
    <div class="sheet-head"><h2>Мины</h2><button class="close" onclick="closeModal()">×</button></div>
    <div class="multiplier-big" id="mineX">1.00x</div>
    <div class="mines-grid" id="minesGrid"></div>
    <button class="btn" id="mineStart" onclick="startMines()">Новая игра</button>
    <button class="btn" id="mineCash" style="display:none;background:#16b77a" onclick="cashMines()">Забрать приз</button>
  `);
}
let MINES_ID=null;
async function startMines(){
  try{const d=await api('/api/games/mines/start',{method:'POST',body:JSON.stringify({mines:4})}); MINES_ID=d.game_id; const g=document.querySelector('#minesGrid'); g.innerHTML=Array.from({length:25},(_,i)=>`<button class="mine-cell" onclick="openMine(${i})">?</button>`).join(''); document.querySelector('#mineStart').style.display='none';document.querySelector('#mineCash').style.display='block';document.querySelector('#mineX').textContent='1.00x';}
  catch(e){toast(e.message)}
}
async function openMine(cell){
  if(!MINES_ID)return;
  try{const d=await api('/api/games/mines/open',{method:'POST',body:JSON.stringify({game_id:MINES_ID,cell})}); const el=document.querySelectorAll('.mine-cell')[cell]; if(el){el.classList.add(d.mine?'mine':'open');el.textContent=d.mine?'×':'◆';el.disabled=true;} if(d.mine){playSound('mine');toast('Мина! Раунд закончен');document.querySelector('#mineCash').style.display='none';MINES_ID=null;}else{document.querySelector('#mineX').textContent=d.multiplier.toFixed(2)+'x';playSound('mines_click');}}catch(e){toast(e.message)}}
async function cashMines(){if(!MINES_ID)return;try{const d=await api('/api/games/mines/cashout',{method:'POST',body:JSON.stringify({game_id:MINES_ID})});STATE.user=d.user;renderUser();toast('Приз забран: '+d.reward+' M');playSound('gift_win');MINES_ID=null;document.querySelector('#mineCash').style.display='none';}catch(e){toast(e.message)}}

function openReferrals(){
  const username=tg?.initDataUnsafe?.user?.username || '';
  const link=`https://t.me/${location.hostname ? 'YOUR_BOT_USERNAME' : 'YOUR_BOT_USERNAME'}?start=ref_${STATE.user.id}`;
  modal(`
    <div class="sheet-head"><h2>Рефералы</h2>
    <button class="close" onclick="closeModal()">×</button></div>
    <div class="card" style="padding:25px;text-align:center">
      <div style="font-size:24px;font-weight:950">Приглашай друзей</div>
      <p style="color:var(--muted)">Твоя реферальная ссылка:</p>
      <input class="input" value="${link}" readonly>
      <button class="btn" onclick="navigator.clipboard.writeText('${link}');toast('Скопировано')">Скопировать ссылку</button>
    </div>
  `);
}

async function showHistory(){
  try{
    const d=await api('/api/history');
    modal(`
      <div class="sheet-head"><h2>История</h2>
      <button class="close" onclick="closeModal()">×</button></div>
      ${d.items.length ? d.items.map(x=>`
        <div class="row-card" style="box-shadow:none;border-bottom:1px solid #eef2f5">
          <div class="row-main">
            <div class="row-title">${escapeHtml(x.description)}</div>
            <div class="row-sub">${new Date(x.created_at*1000).toLocaleString()}</div>
          </div>
          <div class="reward">${x.amount>0?'+':''}${x.amount}</div>
        </div>`).join('') :
        `<p style="color:var(--muted)">История пуста.</p>`}
    `);
  }catch(e){toast(e.message)}
}

function renderHome(){renderUser();renderCases();renderTasks()}
function renderGames(){
  $('coinGameImg')?.setAttribute('src',ASSETS.coin_game);
  $('upgradeGameImg').src=ASSETS.upgrade;
  $('extraGameImg').src=ASSETS.game_extra;
  $('minesGameImg').src=ASSETS.mines;
}
function renderProfile(){
  renderUser();
  if(STATE.user?.is_admin) renderAdmin();
}

async function load(){
  // Telegram injects initData only when the page is opened as a Telegram Mini App.
  // If the Render URL is opened directly in Chrome/Safari, keep the visual app
  // available instead of replacing the whole page with an "empty initData" error.
  const hasTelegramInitData = !!(tg && tg.initData);

  if(!hasTelegramInitData){
    STATE.user={
      id:0,
      username:'preview',
      first_name:'BEAR',
      coins:0,
      stars_spent:0,
      is_admin:false
    };
    STATE.tasks=[];
    STATE.cases=[
      {key:'noob',name:'Noob',price:300,image:ASSETS.case_noob},
      {key:'cash',name:'Big Cash',price:900,image:ASSETS.case_cash},
      {key:'business',name:'Bussines',price:1900,image:ASSETS.case_business}
    ];
    STATE.history=[];
    renderUser();
    renderHome();
    renderGames();
    $('loading').style.display='none';
    return;
  }

  try{
    const d=await api('/api/bootstrap');
    STATE.user=d.user;
    STATE.tasks=d.tasks;
    STATE.cases=d.cases;
    STATE.history=d.history;
    renderUser();
    renderHome();
    renderGames();
    if(STATE.user?.is_admin)renderAdmin();
    $('loading').style.display='none';
  }catch(e){
    $('loading').innerHTML=
      `<div style="padding:30px;text-align:center">
        <b>Не удалось открыть BEAR BOT</b>
        <p style="color:#8c9baa">${escapeHtml(e.message)}</p>
        <button class="btn" style="margin-top:14px" onclick="load()">Повторить</button>
      </div>`;
  }
}

function renderAdmin(){
  const area=$('adminArea');
  area.innerHTML=`
    <div class="section-title"><h2>Админ-панель</h2></div>
    <div class="admin-card">
      <div class="admin-title">Добавить задание</div>
      <div class="form-label">Название</div>
      <input id="aTitle" class="input" placeholder="Например: Подписка на канал">
      <div class="form-label">Описание</div>
      <input id="aDesc" class="input" placeholder="Выполни действие">
      <div class="form-label">Ссылка</div>
      <input id="aUrl" class="input" placeholder="https://t.me/...">
      <div class="form-label">Награда в монетах</div>
      <input id="aReward" class="input" type="number" value="50">
      <button class="btn" onclick="adminAddTask()">Добавить задание</button>
    </div>
    <div id="adminTasks"></div>
  `;
  api('/api/admin/tasks').then(d=>{
    $('adminTasks').innerHTML=d.tasks.map(t=>`
      <div class="admin-card">
        <div class="admin-title">${escapeHtml(t.title)}</div>
        <div style="color:var(--muted);margin-top:5px">${escapeHtml(t.description)}</div>
        <div style="margin-top:8px;color:var(--blue);font-weight:900">+${t.reward} M</div>
        <button class="btn danger" onclick="adminDeleteTask(${t.id})">Удалить</button>
      </div>`).join('');
  }).catch(()=>{});
}

async function adminAddTask(){
  try{
    await api('/api/admin/tasks',{
      method:'POST',
      body:JSON.stringify({
        title:$('aTitle').value,
        description:$('aDesc').value,
        url:$('aUrl').value,
        reward:Number($('aReward').value||50)
      })
    });
    toast('Задание добавлено');
    renderAdmin();
    const d=await api('/api/bootstrap');
    STATE.tasks=d.tasks;renderTasks();
  }catch(e){toast(e.message)}
}

async function adminDeleteTask(id){
  try{
    await api('/api/admin/tasks/'+id,{method:'DELETE'});
    toast('Удалено');
    renderAdmin();
  }catch(e){toast(e.message)}
}

load();
</script>
</body>
</html>
"""

# ============================================================
# API ROUTES
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    page = HTML_PAGE.replace(
        "__ASSETS_JSON__",
        json.dumps(ASSETS, ensure_ascii=False)
    ).replace(
        "__SOUNDS_JSON__",
        json.dumps(SOUNDS, ensure_ascii=False)
    )
    return HTMLResponse(page)

@app.get("/api/webapp")
async def webapp_info():
    return {"webapp_url": WEBAPP_URL, "assets_source": "bot.py", "mini_app": True}

@app.get("/health")
async def health():
    return {"ok": True, "service": "bear-bot"}

@app.get("/api/bootstrap")
async def bootstrap(request: Request):
    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    uid = int(tg_user["id"])
    tasks = db_all("""
        SELECT t.*, CASE WHEN tc.user_id IS NULL THEN 0 ELSE 1 END AS done
        FROM tasks t
        LEFT JOIN task_claims tc
          ON tc.task_id=t.id AND tc.user_id=?
        WHERE t.active=1
        ORDER BY t.id DESC
    """, (uid,))

    history = db_all("""
        SELECT c.*, 
               CASE c.reward_key
                 WHEN 'bear' THEN ?
                 WHEN 'heart' THEN ?
                 WHEN 'cake' THEN ?
                 WHEN 'rocket' THEN ?
                 WHEN 'racket' THEN ?
                 WHEN 'diamond' THEN ?
                 ELSE ?
               END AS image
        FROM case_opens c
        ORDER BY c.id DESC LIMIT 10
    """, (
        ASSETS["bear"], ASSETS["heart"], ASSETS["cake"],
        ASSETS["rocket"], ASSETS["racket"], ASSETS["diamond"],
        ASSETS["coin"]
    ))

    cases = []
    for key, c in CASES.items():
        cases.append({
            "key": key,
            "name": c["name"],
            "price": c["price"],
            "image": c["image"],
            "rewards": [
                {
                    "key": rk,
                    "name": rn,
                    "chance": chance,
                    "image": REWARD_IMAGES.get(rk, ASSETS["coin"])
                }
                for rk, rn, chance in c["rewards"]
            ]
        })

    return {
        "user": public_user(uid),
        "tasks": [dict(x) for x in tasks],
        "cases": cases,
        "history": [dict(x) for x in history],
    }

@app.post("/api/tasks/{task_id}/claim")
async def claim_task(task_id: int, request: Request):
    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    uid = int(tg_user["id"])
    task = db_one("SELECT * FROM tasks WHERE id=? AND active=1", (task_id,))
    if not task:
        raise HTTPException(404, "Задание не найдено")

    already = db_one(
        "SELECT 1 FROM task_claims WHERE user_id=? AND task_id=?",
        (uid, task_id)
    )
    if already:
        raise HTTPException(400, "Задание уже выполнено")

    # IMPORTANT:
    # This confirms the claim server-side. For production tasks that
    # require actual channel membership/subscription verification,
    # add Telegram Bot API checks for channels where the bot is an admin.
    # Do not pretend that simply opening a URL proves subscription.
    db_exec(
        "INSERT INTO task_claims(user_id,task_id,claimed_at) VALUES(?,?,?)",
        (uid, task_id, now())
    )
    change_coins(uid, int(task["reward"]), "task", task["title"])

    rows = db_all("""
        SELECT t.*, CASE WHEN tc.user_id IS NULL THEN 0 ELSE 1 END AS done
        FROM tasks t
        LEFT JOIN task_claims tc
          ON tc.task_id=t.id AND tc.user_id=?
        WHERE t.active=1
        ORDER BY t.id DESC
    """, (uid,))

    return {
        "reward": int(task["reward"]),
        "user": public_user(uid),
        "tasks": [dict(x) for x in rows],
    }

@app.post("/api/cases/{case_key}/open")
async def open_case(case_key: str, request: Request):
    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    if case_key not in CASES:
        raise HTTPException(404, "Кейс не найден")

    uid = int(tg_user["id"])
    c = CASES[case_key]
    u = user_data(uid)

    if u["coins"] < c["price"]:
        raise HTTPException(400, "Недостаточно монет")

    # Charge before reward creation.
    change_coins(uid, -c["price"], "case", f"Открытие кейса {c['name']}")

    reward_key, reward_name, chance = weighted_reward(case_key)

    # Virtual item rewards have no cash redemption here.
    # Coin rewards are credited immediately.
    if reward_key in COIN_REWARDS:
        change_coins(
            uid,
            COIN_REWARDS[reward_key],
            "case_reward",
            f"Награда: {reward_name}"
        )

    db_exec(
        "INSERT INTO case_opens(user_id,case_key,reward_key,reward_name,created_at) "
        "VALUES(?,?,?,?,?)",
        (uid, case_key, reward_key, reward_name, now())
    )

    rare = chance <= 2.0

    return {
        "user": public_user(uid),
        "result": {
            "reward_key": reward_key,
            "reward_name": reward_name,
            "chance": chance,
            "image": REWARD_IMAGES.get(reward_key, ASSETS["coin"]),
            "rare": rare,
            "case_name": c["name"],
        }
    }

@app.get("/api/history")
async def history(request: Request):
    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    uid = int(tg_user["id"])
    rows = db_all(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 50",
        (uid,)
    )
    return {"items": [dict(x) for x in rows]}

@app.post("/api/payments/invoice")
async def invoice(request: Request):
    if not bot:
        raise HTTPException(500, "BOT_TOKEN не настроен")

    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    body = await request.json()
    stars = int(body.get("stars", 0))
    if stars not in (10, 50, 100, 500):
        raise HTTPException(400, "Недопустимое количество Stars")

    uid = int(tg_user["id"])
    payload = make_invoice_payload(uid, stars)

    link = await bot.create_invoice_link(
        title=f"BEAR BOT — {stars} Stars",
        description=f"Пополнение внутреннего баланса на {stars * 10} монет",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label=f"{stars} Stars", amount=stars)],
    )

    return {"invoice_link": link}

# ============================================================
# GAMES
# ============================================================

@app.post("/api/games/coin")
async def coin_game(request: Request):
    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    uid = int(tg_user["id"])
    body = await request.json()
    side = body.get("side")
    if side not in ("heads", "tails"):
        raise HTTPException(400, "Неверная сторона")

    # Free game: no paid stake.
    result = random.choice(["heads", "tails"])
    win = result == side

    if win:
        change_coins(uid, 100, "game_win", "Победа в Монетке")

    return {
        "result": result,
        "win": win,
        "user": public_user(uid)
    }

@app.post("/api/games/upgrade")
async def upgrade_game(request: Request):
    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    uid = int(tg_user["id"])

    # Free demonstration upgrade. It does not consume paid currency.
    win = random.random() < 0.72
    degrees = random.randint(1440, 2160) + random.randint(0, 359)

    if win:
        change_coins(uid, 150, "upgrade_win", "Успешный апгрейд")

    return {
        "win": win,
        "degrees": degrees,
        "user": public_user(uid)
    }

@app.post("/api/games/wheel")
async def wheel_game(request: Request):
    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    uid = int(tg_user["id"])
    rewards = [0, 25, 50, 75, 100, 150, 200, 300]
    weights = [30, 20, 16, 12, 8, 6, 5, 3]
    reward = random.choices(rewards, weights=weights, k=1)[0]

    if reward:
        change_coins(uid, reward, "wheel", "Награда колеса")

    return {
        "reward": reward,
        "degrees": random.randint(1440, 3600),
        "user": public_user(uid)
    }

# Virtual games: no Stars stake; rewards are internal points/items.
@app.post("/api/games/racket")
async def racket_game(request: Request):
    try: tg_user=auth_user_from_request(request)
    except Exception as e: raise HTTPException(401,str(e))
    uid=int(tg_user["id"]); win=random.random()<0.58; mult=round(random.uniform(1.15,3.80),2)
    reward=int(50*mult) if win else 0
    if reward: change_coins(uid,reward,"racket_win",f"Ракетка ×{mult}")
    return {"win":win,"multiplier":mult,"reward":reward,"user":public_user(uid)}

@app.post("/api/games/mines/start")
async def mines_start(request: Request):
    try: tg_user=auth_user_from_request(request)
    except Exception as e: raise HTTPException(401,str(e))
    uid=int(tg_user["id"]); gid=secrets.token_hex(12); mines=random.sample(range(25),4)
    db_exec("INSERT INTO mines_games(id,user_id,mines_count,mine_cells,opened_cells,multiplier,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(gid,uid,4,json.dumps(mines),json.dumps([]),1.0,"active",now()))
    return {"game_id":gid,"mines":4}

@app.post("/api/games/mines/open")
async def mines_open(request: Request):
    try: tg_user=auth_user_from_request(request)
    except Exception as e: raise HTTPException(401,str(e))
    uid=int(tg_user["id"]); body=await request.json(); gid=str(body.get("game_id","")); cell=int(body.get("cell",-1))
    row=db_one("SELECT * FROM mines_games WHERE id=? AND user_id=? AND status='active'",(gid,uid))
    if not row: raise HTTPException(404,"Игра не найдена")
    if cell<0 or cell>=25: raise HTTPException(400,"Неверная клетка")
    mines=json.loads(row["mine_cells"]); opened=json.loads(row["opened_cells"])
    if cell in opened: raise HTTPException(400,"Клетка уже открыта")
    if cell in mines:
        db_exec("UPDATE mines_games SET status='lost',ended_at=? WHERE id=?",(now(),gid)); return {"mine":True,"multiplier":row["multiplier"],"user":public_user(uid)}
    opened.append(cell); mult=round(1.0+len(opened)*0.18,2)
    db_exec("UPDATE mines_games SET opened_cells=?,multiplier=? WHERE id=?",(json.dumps(opened),mult,gid))
    return {"mine":False,"multiplier":mult,"opened":len(opened)}

@app.post("/api/games/mines/cashout")
async def mines_cashout(request: Request):
    try: tg_user=auth_user_from_request(request)
    except Exception as e: raise HTTPException(401,str(e))
    uid=int(tg_user["id"]); body=await request.json(); gid=str(body.get("game_id",""))
    row=db_one("SELECT * FROM mines_games WHERE id=? AND user_id=? AND status='active'",(gid,uid))
    if not row: raise HTTPException(400,"Раунд уже завершён")
    reward=max(10,int(float(row["multiplier"])*80)); db_exec("UPDATE mines_games SET status='cashed',ended_at=? WHERE id=?",(now(),gid)); change_coins(uid,reward,"mines_cashout",f"Мины ×{row['multiplier']}")
    return {"reward":reward,"user":public_user(uid)}

# ============================================================
# ADMIN
# ============================================================

def require_admin(request: Request):
    try:
        tg_user = auth_user_from_request(request)
    except Exception as e:
        raise HTTPException(401, str(e))

    uid = int(tg_user["id"])
    if not is_admin(uid):
        raise HTTPException(403, "Нет доступа")
    return uid

@app.get("/api/admin/tasks")
async def admin_tasks(request: Request):
    require_admin(request)
    rows = db_all("SELECT * FROM tasks ORDER BY id DESC")
    return {"tasks": [dict(x) for x in rows]}

@app.post("/api/admin/tasks")
async def admin_add_task(request: Request):
    require_admin(request)
    body = await request.json()

    title = str(body.get("title", "")).strip()
    description = str(body.get("description", "")).strip()
    url = str(body.get("url", "")).strip()
    reward = int(body.get("reward", 50))

    if not title:
        raise HTTPException(400, "Введите название")
    if not url:
        raise HTTPException(400, "Введите ссылку")
    if reward <= 0 or reward > 100000:
        raise HTTPException(400, "Некорректная награда")

    db_exec(
        "INSERT INTO tasks(title,description,url,reward,type,active,created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (title, description, url, reward, "link", 1, now())
    )
    return {"ok": True}

@app.delete("/api/admin/tasks/{task_id}")
async def admin_delete_task(task_id: int, request: Request):
    require_admin(request)
    db_exec("UPDATE tasks SET active=0 WHERE id=?", (task_id,))
    return {"ok": True}

# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    print("========================================")
    print(" BEAR BOT")
    print(" Telegram Bot + Mini App")
    print("========================================")
    print(f"PORT={PORT}")
    print(f"OWNER_ID={OWNER_ID}")
    print(f"WEBAPP_URL={WEBAPP_URL or '[not set]'}")

    if not BOT_TOKEN:
        print("WARNING: BOT_TOKEN is missing.")

    uvicorn.run(
        "bot:app",
        host="0.0.0.0",
        port=PORT,
        reload=False
    )
