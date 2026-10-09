"""Descarga páginas (Bright Data Web Unlocker o requests) y utilidades de parseo."""
import re
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as _md

import config

BRIGHTDATA_ENDPOINT = "https://api.brightdata.com/request"
LISTING_ID_RE = re.compile(r"/inmueble/(\d+)")
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


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


def _brightdata_fetch(url: str) -> str:
    """HTML renderizado por Bright Data Web Unlocker (salta JS y anti-bots)."""
    resp = requests.post(
        BRIGHTDATA_ENDPOINT,
        headers={
            "Authorization": f"Bearer {config.BRIGHTDATA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"zone": config.BRIGHTDATA_ZONE, "url": url, "format": "raw"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.text


def fetch_html(search_url: str) -> str:
    """(Idealista) búsqueda ordenada por fecha vía Bright Data."""
    return _brightdata_fetch(_ordered_url(search_url))


def fetch_page(url: str, force_render: bool = False) -> str:
    """(Agencias) HTML de la página.

    Intenta primero con un request normal (gratis). Si la web es JavaScript y
    devuelve una cáscara vacía, reintenta con Bright Data (que renderiza el JS).
    """
    if not force_render:
        try:
            r = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=30)
            if r.ok:
                soup = BeautifulSoup(r.text, "html.parser")
                for t in soup(["script", "style", "noscript"]):
                    t.decompose()
                text = soup.get_text(" ", strip=True)
                if len(text) > 1500:  # texto real; si es cáscara JS, caemos a render
                    return r.text
        except requests.RequestException:
            pass
    return _brightdata_fetch(url)


def to_markdown(html: str, max_chars: int = 50000) -> str:
    """Convierte el HTML a markdown compacto (conserva enlaces y precios).

    Markdown ocupa mucho menos que el HTML y mantiene lo que el extractor
    necesita, así que abarata y simplifica la llamada a Claude.
    """
    m = _md(html, strip=["script", "style", "nav", "footer", "header", "svg", "img"])
    m = "\n".join(line for line in m.splitlines() if line.strip())
    return m[:max_chars]


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
