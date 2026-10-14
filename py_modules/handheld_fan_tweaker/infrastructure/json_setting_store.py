from __future__ import annotations

import json
import os
import tempfile

FILE_NAME = "settings.json"
FILE_MODE = 0o644


class JsonSettingStore:
    def __init__(self, directory: str) -> None:
        self._dir = directory
        self._path = os.path.join(directory, FILE_NAME)

    def get(self, key: str, default: str) -> str:
        value = self._load().get(key, default)
        return value if isinstance(value, str) else default

    def put(self, key: str, value: str) -> None:
        data = self._load()
        data[key] = value
        os.makedirs(self._dir, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".settings-", dir=self._dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            os.chmod(tmp, FILE_MODE)
            os.replace(tmp, self._path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def _load(self) -> dict:
        try:
            with open(self._path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}
