"""Survey de todas las fuentes: cuántos anuncios detecta y cuántos pasan el filtro.

Sirve para ver qué agencias funcionan de una y cuáles necesitan trato especial.
No manda nada ni toca el estado.
"""
import csv

import config
import extract
import filters
import scraper

with open(config.FUENTES_PATH, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"{'AGENCIA':22} {'DETECT':>6} {'PASAN':>6}  NOTA")
print("-" * 60)
for row in rows:
    name, url = row["nombre"], row["url"]
    try:
        html = scraper.fetch_page(url)
        mkd = scraper.to_markdown(html)
        listings = extract.extract_listings(mkd, base_url=url, agency=name)
        kept = [l for l in listings if filters.keep(l, config.MAX_PRICE, config.HOUSING_ONLY)]
        nota = "" if listings else "revisar (0 detectados: ¿SPA/JS?)"
        print(f"{name:22} {len(listings):6} {len(kept):6}  {nota}")
    except Exception as e:  # noqa: BLE001
        print(f"{name:22} {'ERR':>6} {'-':>6}  {repr(e)[:60]}")
