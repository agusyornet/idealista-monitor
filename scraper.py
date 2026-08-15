"""Descarga la página de resultados vía Bright Data Web Unlocker y extrae los anuncios."""
import re
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

import config

BRIGHTDATA_ENDPOINT = "https://api.brightdata.com/request"
LISTING_ID_RE = re.compile(r"/inmueble/(\d+)")


@dataclass
class Listing:
    listing_id: str
    url: str
    title: str = ""
    price: str = ""
    details: list[str] = field(default_factory=list)
    description: str = ""


def _ordered_url(search_url: str) -> str:
    """Añade el orden por fecha de publicación si no está ya en la URL."""
    if "ordenado-por" in search_url:
        return search_url
    sep = "&" if "?" in search_url else "?"
    return f"{search_url}{sep}ordenado-por=fecha-publicacion-desc"


def fetch_html(search_url: str) -> str:
    """Devuelve el HTML de la búsqueda, resuelto por Bright Data Web Unlocker.

    Web Unlocker salta DataDome por su cuenta y devuelve el HTML ya renderizado.
    Solo pagas los requests que salen bien.
    """
    resp = requests.post(
        BRIGHTDATA_ENDPOINT,
        headers={
            "Authorization": f"Bearer {config.BRIGHTDATA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "zone": config.BRIGHTDATA_ZONE,
            "url": _ordered_url(search_url),
            "format": "raw",
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.text


def parse_listings(html: str) -> list[Listing]:
    """Extrae los anuncios de la página de resultados.

    Idealista renombra clases de vez en cuando, así que combinamos varias
    estrategias: primero los <article> con data-element-id, y si no,
    cualquier enlace a /inmueble/<id>/.
    """
    soup = BeautifulSoup(html, "html.parser")
    listings: dict[str, Listing] = {}

    for article in soup.select("article.item, article[data-element-id]"):
        lid = article.get("data-element-id")
        link = article.select_one("a.item-link") or article.find(
            "a", href=LISTING_ID_RE
        )
        if not lid and link and link.get("href"):
            m = LISTING_ID_RE.search(link["href"])
            lid = m.group(1) if m else None
        if not lid:
            continue

        href = link["href"] if link and link.get("href") else f"/inmueble/{lid}/"
        url = href if href.startswith("http") else f"https://www.idealista.com{href}"

        price_el = article.select_one(".item-price")
        desc_el = article.select_one(".item-description, p.ellipsis")

        listings[lid] = Listing(
            listing_id=lid,
            url=url,
            title=(link.get("title") or link.get_text(strip=True)) if link else "",
            price=price_el.get_text(" ", strip=True) if price_el else "",
            details=[d.get_text(strip=True) for d in article.select(".item-detail")],
            description=desc_el.get_text(" ", strip=True) if desc_el else "",
        )

    # Fallback: si el layout cambió y no encontramos articles, barremos enlaces.
    if not listings:
        for a in soup.find_all("a", href=LISTING_ID_RE):
            m = LISTING_ID_RE.search(a["href"])
            if not m:
                continue
            lid = m.group(1)
            if lid in listings:
                continue
            href = a["href"]
            url = href if href.startswith("http") else f"https://www.idealista.com{href}"
            listings[lid] = Listing(
                listing_id=lid, url=url, title=a.get_text(strip=True)
            )

    return list(listings.values())


def looks_blocked(html: str) -> bool:
    """Heurística para detectar un captcha / bloqueo de DataDome."""
    low = html.lower()
    return "datadome" in low or "captcha-delivery" in low or len(html) < 2000
