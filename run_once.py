"""Un solo chequeo, para GitHub Actions (sin bucle).

Chequea Idealista una vez, avisa de lo nuevo por Telegram, guarda el estado y
termina. GitHub Actions lo dispara cada 30 min con un cron. El filtro de horario
(6am-2am, hora de España) se hace aquí, así el cron puede ser simple en UTC.
"""
import logging
import sys

import config
import main  # reutilizamos check_once() e in_active_window()
from store import SeenStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("idealista-bot")


def run() -> None:
    problems = config.validate()
    if problems:
        log.error("Configuración incompleta:\n - %s", "\n - ".join(problems))
        sys.exit(1)

    if not main.in_active_window():
        log.info("Fuera de horario activo (%02d:00-%02d:00, %s). No hago nada.",
                 config.ACTIVE_START_HOUR, config.ACTIVE_END_HOUR, config.TIMEZONE)
        return

    store = SeenStore(config.DB_PATH)
    main.check_once(store)


if __name__ == "__main__":
    run()
