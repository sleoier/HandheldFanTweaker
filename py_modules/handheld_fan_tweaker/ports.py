from __future__ import annotations

from typing import Dict, Optional, Protocol, Sequence

from .domain import Cluster, FanCurve, Snapshot, Telemetry


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


class CpuFrequencyControl(Protocol):
    def clusters(self) -> Sequence[Cluster]: ...

    def current_max(self, cluster: str) -> Optional[int]: ...

    def set_max(self, cluster: str, khz: int) -> None: ...


class SettingStore(Protocol):
    def get(self, key: str, default: str) -> str: ...

    def put(self, key: str, value: str) -> None: ...
