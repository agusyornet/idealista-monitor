"""Un chequeo de todas las agencias de fuentes.csv (para GitHub Actions / local).

Por cada agencia: descarga -> markdown -> (si la página cambió) Claude extrae ->
filtra vivienda + <= MAX_PRICE -> avisa por Telegram los anuncios nuevos.

- Detección por firma de enlaces: si no aparecen anuncios nuevos, no llama a Claude.
- Primer arranque: marca lo existente como visto SIN avisar (para no inundarte).
- El horario (CHECK_HOURS, hora de España) se filtra aquí.
"""
from __future__ import annotations

import csv
import hashlib
import logging
import os
import re
import sys
from datetime import datetime

import config
import extract
import filters
import scraper
import notifier
from agency_state import AgencyState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("agencias-bot")

_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")  # objetivos de enlaces markdown


def _now_madrid() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(config.TIMEZONE))
    except Exception:  # noqa: BLE001
        return datetime.now()


def in_check_hour() -> bool:
    return _now_madrid().hour in set(config.CHECK_HOURS)


def signature(markdown: str) -> str:
    """Firma del conjunto de enlaces de la página (cambia si aparece un anuncio nuevo)."""
    links = sorted(set(_LINK_RE.findall(markdown)))
    return hashlib.sha256("\n".join(links).encode("utf-8")).hexdigest()


def validate() -> list[str]:
    problems = []
    if not config.BRIGHTDATA_API_KEY or not config.BRIGHTDATA_ZONE:
        problems.append("Falta BRIGHTDATA_API_KEY o BRIGHTDATA_ZONE")
    if not config.ANTHROPIC_API_KEY:
        problems.append("Falta ANTHROPIC_API_KEY")
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        problems.append("Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    return problems


def load_fuentes():
    with open(config.FUENTES_PATH, encoding="utf-8") as f:
        return [(r["nombre"], r["url"]) for r in csv.DictReader(f) if r.get("url")]


def process_agency(name: str, url: str, state: AgencyState, first_run: bool) -> int:
    """Procesa una agencia. Devuelve cuántos anuncios nuevos avisó."""
    html = scraper.fetch_page(url)
    mkd = scraper.to_markdown(html)

    sig = signature(mkd)
    if state.page_hash(url) == sig:
        log.info("[%s] sin cambios.", name)
        return 0
    state.set_page_hash(url, sig)

    listings = extract.extract_listings(mkd, base_url=url, agency=name)
    kept = [l for l in listings if filters.keep(l, config.MAX_PRICE, config.HOUSING_ONLY)]
    log.info("[%s] %d detectados, %d pasan filtro.", name, len(listings), len(kept))

    avisados = 0
    for l in kept:
        if state.seen(l.url):
            continue
        if first_run:
            state.mark_seen(l.url)  # primer arranque: marca sin avisar
            continue
        try:
            notifier.send_agency(l)
            state.mark_seen(l.url)
            avisados += 1
            log.info("[%s] avisado: %s (%s EUR)", name, l.url, l.price_eur)
        except Exception as e:  # noqa: BLE001
            log.error("[%s] fallo al avisar %s: %s", name, l.url, e)
    return avisados


def run() -> None:
    problems = validate()
    if problems:
        log.error("Config incompleta:\n - %s", "\n - ".join(problems))
        sys.exit(1)

    force = os.getenv("FORCE_RUN", "").strip().lower() in ("1", "true", "yes")
    if not force and not in_check_hour():
        log.info("Fuera de horario (%s, %s). No hago nada.",
                 config.CHECK_HOURS, config.TIMEZONE)
        return

    state = AgencyState(config.AGENCY_STATE_PATH)
    first_run = state.is_empty()
    if first_run:
        log.info("Primer arranque: marcaré lo existente como visto SIN avisar.")

    total = 0
    for name, url in load_fuentes():
        try:
            total += process_agency(name, url, state, first_run)
        except Exception as e:  # noqa: BLE001
            log.error("[%s] error: %s", name, e)

    state.save()
    log.info("Hecho. %d aviso(s) enviado(s).", total)


if __name__ == "__main__":
    run()
