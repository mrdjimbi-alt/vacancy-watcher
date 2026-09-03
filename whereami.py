# -*- coding: utf-8 -*-
"""Показывает, кто бот и в какие чаты его добавили.

Нужен, чтобы узнать id канала: добавь бота админом, напиши в канал любое
сообщение и запусти этот скрипт. Он покажет id, который надо вписать в TG_CHAT.
"""
import os
import sys
from pathlib import Path

import requests

HERE = Path(__file__).parent


def load_env():
    path = HERE / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
token = os.environ.get("TG_TOKEN")
if not token:
    print("нет TG_TOKEN")
    sys.exit(1)

api = f"https://api.telegram.org/bot{token}"

me = requests.get(f"{api}/getMe", timeout=20).json()
if not me.get("ok"):
    print("токен не принят:", me.get("description"))
    sys.exit(1)
bot = me["result"]
print(f"бот: @{bot['username']} ({bot['first_name']}), id {bot['id']}")

updates = requests.get(f"{api}/getUpdates", timeout=20).json()
if not updates.get("ok"):
    print("getUpdates:", updates.get("description"))
    sys.exit(1)

seen = {}
for upd in updates["result"]:
    for key in ("message", "channel_post", "my_chat_member", "edited_channel_post"):
        item = upd.get(key)
        if not item:
            continue
        chat = item["chat"]
        seen[chat["id"]] = (chat.get("type"), chat.get("title") or chat.get("username"))

        # если сообщение переслали из канала, id канала виден в источнике —
        # это запасной путь, когда бота в канал добавили, а писать там некому
        origin = item.get("forward_from_chat") or item.get("forward_origin", {}).get("chat")
        if origin:
            seen[origin["id"]] = (origin.get("type"),
                                  origin.get("title") or origin.get("username"))

if not seen:
    print("\nчатов пока не видно.")
    print("добавь бота админом в канал и напиши там любое сообщение, потом запусти снова.")
    print("(бот видит только то, что было после его добавления)")
else:
    print("\nчаты, которые видит бот:")
    for chat_id, (chat_type, title) in seen.items():
        mark = "  <-- канал" if chat_type == "channel" else ""
        print(f"  {chat_id}  {chat_type:<10} {title}{mark}")
    print("\nнужный id впиши в .env как TG_CHAT")
