from __future__ import annotations

import json
import os
import tempfile

from ..domain import Snapshot

FILE_NAME = "curves.json"
FILE_MODE = 0o644


class JsonSnapshotStore:
    def __init__(self, directory: str) -> None:
        self._dir = directory
        self._path = os.path.join(directory, FILE_NAME)

    def load(self) -> Snapshot:
        try:
            with open(self._path, encoding="utf-8") as fh:
                return Snapshot.from_dict(json.load(fh))
        except (OSError, ValueError, AttributeError):
            return Snapshot()

    def save(self, snapshot: Snapshot) -> None:
        os.makedirs(self._dir, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".curves-", dir=self._dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(snapshot.as_dict(), fh, indent=2)
            os.chmod(tmp, FILE_MODE)  # mkstemp creates 0600
            os.replace(tmp, self._path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
