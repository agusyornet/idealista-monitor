"""Extractor genérico de anuncios con Claude.

Lee el markdown de la página de alquileres de una agencia y devuelve una lista
estructurada de anuncios. Funciona en cualquier web sin parser a medida.
"""
from __future__ import annotations

import json
from urllib.parse import urljoin

import config
from models import AgencyListing

_client = None

SYSTEM = """Extraes anuncios de alquiler de la página (en markdown) de una agencia \
inmobiliaria. Devuelve SOLO un array JSON, sin texto alrededor.

Cada elemento del array es un objeto con estas claves exactas:
- "url": enlace al detalle del anuncio (tal cual aparece, aunque sea relativo).
- "title": título del anuncio.
- "price_eur": alquiler MENSUAL en euros como número entero (sin símbolos ni \
puntos de miles). null si no hay precio claro.
- "property_type": uno de "vivienda", "local", "oficina", "despacho", "parking", "otro".
- "status": uno de "disponible", "reservado", "alquilado", "desconocido".

Reglas:
- Incluye SOLO los anuncios de los resultados principales de la búsqueda.
- IGNORA secciones de "destacados", "similares", "recomendados" o "quizás te \
interese": no son resultados reales de la búsqueda.
- Si la página dice que no hay resultados, devuelve [].
- No inventes anuncios ni precios. Si un dato no está, usa null o "desconocido".
- Un piso/apartamento/ático/estudio/dúplex es "vivienda". Un local comercial es \
"local". Una plaza de garaje es "parking".
"""


def _get_client():
    global _client
    if _client is None:
        import anthropic
        kwargs = {"api_key": config.ANTHROPIC_API_KEY} if config.ANTHROPIC_API_KEY else {}
        _client = anthropic.Anthropic(**kwargs)
    return _client


def _parse_json_array(text: str) -> list:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []


def extract_listings(markdown: str, base_url: str, agency: str) -> list[AgencyListing]:
    resp = _get_client().messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4000,
        system=SYSTEM,
        messages=[{"role": "user", "content": markdown}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    rows = _parse_json_array(text)

    listings: list[AgencyListing] = []
    for r in rows:
        if not isinstance(r, dict) or not r.get("url"):
            continue
        price = r.get("price_eur")
        if isinstance(price, str):
            digits = "".join(ch for ch in price if ch.isdigit())
            price = int(digits) if digits else None
        listings.append(
            AgencyListing(
                agency=agency,
                url=urljoin(base_url, str(r["url"])),
                title=str(r.get("title") or "").strip(),
                price_eur=price if isinstance(price, int) else None,
                property_type=str(r.get("property_type") or "otro").lower().strip(),
                status=str(r.get("status") or "desconocido").lower().strip(),
            )
        )
    return listings
