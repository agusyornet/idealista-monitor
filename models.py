"""Modelo de un anuncio de alquiler de una agencia."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgencyListing:
    agency: str            # nombre/fuente de la agencia
    url: str               # URL absoluta del anuncio (sirve de ID único)
    title: str = ""
    price_eur: int | None = None   # alquiler mensual en EUR (None si no se pudo leer)
    property_type: str = "otro"    # vivienda | local | oficina | despacho | parking | otro
    status: str = "desconocido"    # disponible | reservado | alquilado | desconocido
