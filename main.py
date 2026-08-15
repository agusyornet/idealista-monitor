"""Bucle principal: chequea Idealista, detecta anuncios nuevos y avisa por Telegram.

Diseño: 1 request por ciclo (la página de resultados ordenada por fecha). Solo
cuando aparece un ID nuevo se redacta el borrador y se envía el aviso. Tú mandas
el mensaje a mano desde el enlace -> ninguna acción automatizada toca tu cuenta.
"""
from __future__ import annotations

import logging
import random
import sys
import time
from datetime import datetime

import config
import drafter
import notifier
import scraper
from store import SeenStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("idealista-bot")


def _now() -> datetime:
    """Hora actual en la zona configurada (por defecto España)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(config.TIMEZONE))
    except Exception:  # noqa: BLE001
        return datetime.now()  # fallback: hora local de la máquina


def in_active_window(now: datetime | None = None) -> bool:
    """¿Estamos dentro de la franja horaria activa? (soporta cruce de medianoche)."""
    h = (now or _now()).hour
    s, e = config.ACTIVE_START_HOUR, config.ACTIVE_END_HOUR
    if s == e:
        return True
    if s < e:
        return s <= h < e
    return h >= s or h < e  # p.ej. 6 -> 2 cruza medianoche


def check_once(store: SeenStore) -> None:
    html = scraper.fetch_html(config.SEARCH_URL)
    if scraper.looks_blocked(html):
        log.warning("Posible bloqueo/captcha de DataDome. Salto este ciclo.")
        return

    listings = scraper.parse_listings(html)
    log.info("Encontrados %d anuncios en la página.", len(listings))

    if not listings:
        log.warning("0 anuncios: puede que el layout de Idealista haya cambiado.")
        return

    # Primer arranque: marcamos todo lo existente como visto SIN avisar,
    # para no recibir un aluvión de mensajes por anuncios que ya estaban.
    if store.is_empty():
        store.add_many(l.listing_id for l in listings)
        log.info("Primer arranque: %d anuncios marcados como vistos (sin avisar).",
                 len(listings))
        return

    nuevos = [l for l in listings if not store.has(l.listing_id)]
    if not nuevos:
        log.info("Sin novedades.")
        return

    log.info("%d anuncio(s) nuevo(s).", len(nuevos))
    for listing in nuevos:
        try:
            draft = drafter.draft_message(listing)
        except Exception as e:  # noqa: BLE001
            log.error("Fallo al redactar borrador (%s). Aviso sin borrador.", e)
            draft = "(No se pudo generar el borrador automáticamente.)"
        try:
            notifier.send(listing, draft)
            store.add(listing.listing_id)  # solo lo marcamos si el aviso salió bien
            log.info("Avisado: %s", listing.url)
        except Exception as e:  # noqa: BLE001
            log.error("Fallo al enviar aviso de %s: %s", listing.url, e)


def main() -> None:
    problems = config.validate()
    if problems:
        log.error("Configuración incompleta:\n - %s", "\n - ".join(problems))
        log.error("Copia .env.example a .env y rellena los valores.")
        sys.exit(1)

    store = SeenStore(config.DB_PATH)
    log.info("Arrancando. Chequeo cada ~%d min (+/- %d).",
             config.POLL_INTERVAL_MIN, config.POLL_JITTER_MIN)

    while True:
        if not in_active_window():
            log.info("Fuera de horario activo (%02d:00-%02d:00). Duermo 20 min.",
                     config.ACTIVE_START_HOUR, config.ACTIVE_END_HOUR)
            time.sleep(20 * 60)
            continue

        try:
            check_once(store)
        except Exception as e:  # noqa: BLE001
            log.exception("Error en el ciclo: %s", e)

        jitter = random.uniform(-config.POLL_JITTER_MIN, config.POLL_JITTER_MIN)
        sleep_min = max(1.0, config.POLL_INTERVAL_MIN + jitter)
        log.info("Durmiendo %.1f min.", sleep_min)
        time.sleep(sleep_min * 60)


if __name__ == "__main__":
    main()
