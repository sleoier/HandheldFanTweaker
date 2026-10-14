from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Pairs = List[List[int]]


@dataclass(frozen=True)
class Telemetry:
    curve_temp_c: Optional[float]
    hottest_c: Optional[float]
    fan_pwm: Optional[int]
    fan_rpm: Optional[int]

    def as_dict(self) -> dict:
        return {
            "curve_temp_c": self.curve_temp_c,
            "hottest_c": self.hottest_c,
            "fan_pwm": self.fan_pwm,
            "fan_rpm": self.fan_rpm,
        }


@dataclass(frozen=True)
class BackendInfo:
    name: Optional[str]
    profiles: Tuple[str, ...]
    editable: bool
    reason: Optional[str] = None


@dataclass
class Snapshot:
    """factory: the curves found in the config the first time the plugin read it.
    custom: the curves the user applied from the plugin."""

    factory: Dict[str, Pairs] = field(default_factory=dict)
    custom: Dict[str, Pairs] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"version": 1, "factory": self.factory, "custom": self.custom}

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(factory=dict(data.get("factory") or {}), custom=dict(data.get("custom") or {}))
