"""Prueba el extractor sobre UNA página de agencia.

Uso:  python test_extract.py "https://www.vivalco.com/properties/?..."

Hace: descarga la página -> markdown -> Claude extrae anuncios -> aplica filtros
(vivienda + <= MAX_PRICE + no reservado/alquilado) y muestra lo que pasaría y lo
que se descarta. No manda nada por Telegram ni toca el estado.
"""
import sys

import config
import extract
import filters
import scraper

if len(sys.argv) < 2:
    print('Uso: python test_extract.py "<url de la agencia>"')
    raise SystemExit(1)

url = sys.argv[1]

print("1) Descargando página...")
html = scraper.fetch_page(url)
print(f"   HTML: {len(html)} caracteres")

mkd = scraper.to_markdown(html)
print(f"   Markdown: {len(mkd)} caracteres")

print("2) Extrayendo anuncios con Claude...")
listings = extract.extract_listings(mkd, base_url=url, agency="test")
print(f"   Anuncios detectados: {len(listings)}")

print(f"\n3) Filtrando (vivienda={config.HOUSING_ONLY}, max {config.MAX_PRICE} EUR):\n")
kept, dropped = [], []
for l in listings:
    (kept if filters.keep(l, config.MAX_PRICE, config.HOUSING_ONLY) else dropped).append(l)

print(f"--- PASAN EL FILTRO ({len(kept)}) ---")
for l in kept:
    print(f"  [{l.price_eur} EUR] {l.property_type} | {l.title}")
    print(f"      {l.url}")

print(f"\n--- DESCARTADOS ({len(dropped)}) ---")
for l in dropped:
    print(f"  [{l.price_eur} EUR] {l.property_type}/{l.status} | {l.title[:60]}")
