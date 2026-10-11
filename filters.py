"""Filtro de anuncios.

Estrategia LISTA NEGRA (para no perder deptos): descarta solo lo que es
claramente NO-vivienda (local, oficina, parking, etc.). Todo lo demás —
incluido lo dudoso o lo etiquetado como "otro"— pasa. Mejor un falso aviso
que perder una vivienda buena.
"""
from models import AgencyListing

# Tipos que NO son vivienda -> se descartan.
EXCLUDED_TYPES = {
    "local", "oficina", "despacho", "parking", "garaje", "plaza",
    "trastero", "nave", "terreno", "solar", "edificio",
}
DESCARTAR_ESTADO = {"reservado", "alquilado"}


def keep(listing: AgencyListing, max_price: int, housing_only: bool) -> bool:
    if housing_only and listing.property_type in EXCLUDED_TYPES:
        return False
    if listing.status in DESCARTAR_ESTADO:
        return False
    if listing.price_eur is not None and listing.price_eur > max_price:
        return False
    # Sin precio o tipo dudoso -> pasa (mejor sobrar que faltar).
    return True
