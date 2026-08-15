"""Genera el borrador del mensaje para el dueño.

Modos (config.DRAFT_MODE):
- "template": plantilla fija rellenada con los datos del anuncio. Sin API key.
- "claude":   mensaje personalizado con la API de Claude. Necesita ANTHROPIC_API_KEY.
- "none":     sin borrador (solo aviso del anuncio).
"""
import config
from scraper import Listing

_client = None

SYSTEM = """Eres un asistente que redacta mensajes breves y naturales en español \
de España para contactar a un anunciante de Idealista y pedir una visita de un \
piso de alquiler.

Reglas:
- Tono cercano, educado y directo. Nada de sonar a plantilla ni a bot.
- 3-5 frases como mucho. Sin asunto, sin firma con datos de contacto.
- Menciona algo concreto del anuncio (zona, tamaño o precio) para que se note \
que la persona lo ha leído.
- Pide una visita y ofrece disponibilidad.
- Devuelve SOLO el texto del mensaje, sin comillas ni explicaciones."""


def draft_message(listing: Listing) -> str:
    mode = config.DRAFT_MODE
    if mode == "none":
        return ""
    if mode == "claude":
        return _draft_claude(listing)
    return _draft_template(listing)


def _draft_template(listing: Listing) -> str:
    titulo = listing.title or "el piso que has publicado"
    precio = f" ({listing.price})" if listing.price else ""
    perfil = f" {config.TENANT_PROFILE}" if config.TENANT_PROFILE else ""
    firma = f"\n\nUn saludo,\n{config.TENANT_NAME}" if config.TENANT_NAME else ""
    return (
        f"Hola, he visto {titulo}{precio} en Idealista y me interesa mucho. "
        f"Me gustaría concertar una visita.{perfil} "
        f"¿Qué disponibilidad tienes para enseñarlo? Gracias.{firma}"
    )


def _get_client():
    global _client
    if _client is None:
        import anthropic  # import perezoso: solo si se usa el modo claude
        kwargs = {"api_key": config.ANTHROPIC_API_KEY} if config.ANTHROPIC_API_KEY else {}
        _client = anthropic.Anthropic(**kwargs)
    return _client


def _draft_claude(listing: Listing) -> str:
    detalles = ", ".join(listing.details) if listing.details else "sin detalles"
    user = (
        f"Anuncio:\n"
        f"- Título: {listing.title or 'piso en alquiler'}\n"
        f"- Precio: {listing.price or 'no indicado'}\n"
        f"- Detalles: {detalles}\n"
        f"- Descripción: {listing.description or 'no disponible'}\n\n"
        f"Sobre quien escribe:\n"
        f"- Nombre: {config.TENANT_NAME or 'no indicado'}\n"
        f"- Perfil/disponibilidad: {config.TENANT_PROFILE or 'no indicado'}\n\n"
        f"Redacta el mensaje para pedir una visita."
    )
    resp = _get_client().messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=500,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()
