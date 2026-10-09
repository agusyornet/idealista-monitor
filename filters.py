"""Filtro de anuncios: solo vivienda, por debajo del precio máximo, disponible."""
from models import AgencyListing

DESCARTAR_ESTADO = {"reservado", "alquilado"}


def keep(listing: AgencyListing, max_price: int, housing_only: bool) -> bool:
    if housing_only and listing.property_type != "vivienda":
        return False
    if listing.status in DESCARTAR_ESTADO:
        return False
    if listing.price_eur is not None and listing.price_eur > max_price:
        return False
    # Si no hay precio, lo dejamos pasar (mejor un falso positivo que perder uno bueno).
    return True
