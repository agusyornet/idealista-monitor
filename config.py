"""Carga de configuración desde variables de entorno (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "si", "sí")


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


SEARCH_URL = os.getenv("SEARCH_URL", "").strip()

POLL_INTERVAL_MIN = _int("POLL_INTERVAL_MIN", 30)
POLL_JITTER_MIN = _int("POLL_JITTER_MIN", 5)

ACTIVE_START_HOUR = _int("ACTIVE_START_HOUR", 6)
ACTIVE_END_HOUR = _int("ACTIVE_END_HOUR", 2)
# Zona horaria para el horario activo. Así funciona igual en tu Mac o en un VPS (UTC).
TIMEZONE = os.getenv("TIMEZONE", "Europe/Madrid").strip()

BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY", "").strip()
BRIGHTDATA_ZONE = os.getenv("BRIGHTDATA_ZONE", "").strip()

# Borrador del mensaje: "template" (sin key), "claude" (personalizado) o "none".
DRAFT_MODE = os.getenv("DRAFT_MODE", "template").strip().lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5").strip()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

TENANT_NAME = os.getenv("TENANT_NAME", "").strip()
TENANT_PROFILE = os.getenv("TENANT_PROFILE", "").strip()

DB_PATH = os.getenv("DB_PATH", "state.json").strip()


def validate() -> list[str]:
    """Devuelve una lista de problemas de configuración (vacía si todo OK)."""
    problems = []
    if not SEARCH_URL:
        problems.append("Falta SEARCH_URL")
    if not BRIGHTDATA_API_KEY or not BRIGHTDATA_ZONE:
        problems.append("Falta BRIGHTDATA_API_KEY o BRIGHTDATA_ZONE")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        problems.append("Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    if DRAFT_MODE == "claude" and not ANTHROPIC_API_KEY:
        problems.append("DRAFT_MODE=claude necesita ANTHROPIC_API_KEY (o `ant auth login`)")
    return problems
