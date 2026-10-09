"""Estado del bot de agencias: anuncios ya vistos + hash de cada página.

- seen:   {url_anuncio: timestamp}  -> para no avisar dos veces.
- hashes: {url_agencia: firma}      -> si la página no cambió, no llamamos a Claude.

Se guarda en JSON para poder versionarlo en el repo (GitHub Actions lo commitea).
"""
from __future__ import annotations

import json
import os
import time


class AgencyState:
    def __init__(self, path: str):
        self.path = path
        self.data = {"seen": {}, "hashes": {}}
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                self.data["seen"] = d.get("seen", {})
                self.data["hashes"] = d.get("hashes", {})
            except (json.JSONDecodeError, OSError):
                pass

    def is_empty(self) -> bool:
        return not self.data["seen"] and not self.data["hashes"]

    def seen(self, url: str) -> bool:
        return url in self.data["seen"]

    def mark_seen(self, url: str) -> None:
        self.data["seen"][url] = int(time.time())

    def page_hash(self, key: str):
        return self.data["hashes"].get(key)

    def set_page_hash(self, key: str, value: str) -> None:
        self.data["hashes"][key] = value

    def save(self) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=0, sort_keys=True)
        os.replace(tmp, self.path)
