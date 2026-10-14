from __future__ import annotations

from typing import Dict, Optional, Protocol

from .domain import FanCurve, Snapshot, Telemetry


class CurveRepository(Protocol):
    def read_all(self) -> Dict[str, FanCurve]: ...

    def write(self, profile: str, curve: FanCurve) -> None: ...


class DaemonController(Protocol):
    def reload(self) -> None: ...

    def active_profile(self) -> Optional[str]: ...


class TelemetrySource(Protocol):
    def read(self) -> Telemetry: ...


class SnapshotStore(Protocol):
    def load(self) -> Snapshot: ...

    def save(self, snapshot: Snapshot) -> None: ...
