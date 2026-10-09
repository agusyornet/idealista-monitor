"""Envío de avisos por Telegram."""
import requests

import config


def _post(text: str) -> None:
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


def send_agency(listing) -> None:
    """Aviso de un anuncio nuevo de una agencia."""
    precio = f"{listing.price_eur} €/mes" if listing.price_eur else "precio n/d"
    text = (
        f"🏠 <b>{_escape(listing.agency)}</b>\n"
        f"{_escape(listing.title)}\n"
        f"{_escape(precio)}  ·  {_escape(listing.property_type)}\n\n"
        f"{listing.url}"
    )
    _post(text)


def send(listing, draft: str) -> None:
    """(Idealista, legacy) aviso con borrador de mensaje."""
    detalles = " · ".join(listing.details) if getattr(listing, "details", None) else ""
    text = (
        f"🏠 <b>Nuevo anuncio</b>\n"
        f"{_escape(listing.title)}\n"
        f"{_escape(listing.price)}  {_escape(detalles)}\n\n"
        f"{listing.url}"
    )
    if draft:
        text += f"\n\n✍️ <b>Borrador para el dueño:</b>\n{_escape(draft)}"
    _post(text)


def _escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
