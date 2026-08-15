"""Estado persistente (qué anuncios ya vimos), en JSON para poder versionarlo en git."""
import json
import os
import time


class SeenStore:
    def __init__(self, path: str):
        self.path = path
        self._data: dict[str, int] = {}
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def has(self, listing_id: str) -> bool:
        return listing_id in self._data

    def add(self, listing_id: str) -> None:
        self._data[listing_id] = int(time.time())
        self._save()

    def add_many(self, listing_ids) -> None:
        now = int(time.time())
        for lid in listing_ids:
            self._data.setdefault(lid, now)
        self._save()

    def _save(self) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=0, sort_keys=True)
        os.replace(tmp, self.path)
