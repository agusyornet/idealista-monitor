"""Ayudante: detecta tu TELEGRAM_CHAT_ID.

Antes de correrlo:
1. Pon tu TELEGRAM_BOT_TOKEN en el .env.
2. Escríbele algo a tu bot en Telegram (ej. "hola").

Luego: python get_chat_id.py
"""
import requests

import config

if not config.TELEGRAM_BOT_TOKEN:
    print("Falta TELEGRAM_BOT_TOKEN en el .env. Ponlo y vuelve a correr esto.")
    raise SystemExit(1)

url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
data = requests.get(url, timeout=30).json()

if not data.get("ok"):
    print("El token no es válido. Revísalo en @BotFather -> /mybots -> API Token.")
    print("Respuesta:", data)
    raise SystemExit(1)

chats = {}
for upd in data.get("result", []):
    msg = upd.get("message") or upd.get("edited_message") or {}
    chat = msg.get("chat")
    if chat:
        chats[chat["id"]] = chat.get("username") or chat.get("first_name") or ""

if not chats:
    print("No veo mensajes todavía. Escríbele algo a tu bot en Telegram y vuelve a correr esto.")
    raise SystemExit(0)

print("Chats encontrados (usa el número como TELEGRAM_CHAT_ID):")
for cid, name in chats.items():
    print(f"  TELEGRAM_CHAT_ID={cid}   ({name})")
