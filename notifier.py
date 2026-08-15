"""Envío de avisos por Telegram."""
import requests

import config
from scraper import Listing


def send(listing: Listing, draft: str) -> None:
    detalles = " · ".join(listing.details) if listing.details else ""
    text = (
        f"🏠 <b>Nuevo anuncio</b>\n"
        f"{_escape(listing.title)}\n"
        f"{_escape(listing.price)}  {_escape(detalles)}\n\n"
        f"{listing.url}"
    )
    if draft:
        text += f"\n\n✍️ <b>Borrador para el dueño:</b>\n{_escape(draft)}"

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=30,
    )
    resp.raise_for_status()


def _escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
