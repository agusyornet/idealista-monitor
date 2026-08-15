"""Prueba de punta a punta (1 sola vez, sin bucle ni tocar el estado).

Hace: valida config -> pide 1 página a Bright Data -> parsea -> te manda el
primer anuncio por Telegram. Sirve para confirmar que toda la cadena funciona.
"""
import config
import drafter
import notifier
import scraper

problems = config.validate()
if problems:
    print("Config incompleta:\n - " + "\n - ".join(problems))
    raise SystemExit(1)

print("1) Pidiendo la búsqueda a Bright Data Web Unlocker...")
html = scraper.fetch_html(config.SEARCH_URL)
print(f"   HTML recibido: {len(html)} caracteres")

if scraper.looks_blocked(html):
    print("   ⚠️  Parece un bloqueo/captcha. Muestra de lo recibido:")
    print(html[:400])
    raise SystemExit(1)

print("2) Parseando anuncios...")
listings = scraper.parse_listings(html)
print(f"   Anuncios encontrados: {len(listings)}")
for l in listings[:5]:
    print(f"   - {l.listing_id} | {l.title} | {l.price} | {l.details}")

if not listings:
    print("   ⚠️  0 anuncios: revisa la SEARCH_URL o los selectores en scraper.py")
    raise SystemExit(1)

print("3) Enviando el primer anuncio por Telegram...")
first = listings[0]
draft = drafter.draft_message(first)
notifier.send(first, draft)
print("   ✅ Enviado. Revisa Telegram: deberías tener el aviso del anuncio.")
