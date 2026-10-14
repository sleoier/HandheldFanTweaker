from __future__ import annotations

import glob
import os
import re
from typing import List, Optional, Sequence

from ..domain import Telemetry
from .daemons import under

DEFAULT_ZONE_PATTERN = r"cpu|gpu"
DEFAULT_FAN_NAMES = ("pwmfan", "nx669j_fan")
HOTTEST_ZONES_AVERAGED = 3
_SANE_RANGE_C = (-20.0, 150.0)


class SysfsTelemetry:
    def __init__(
        self,
        root: str = "/",
        zone_pattern: str = DEFAULT_ZONE_PATTERN,
        fan_names: Sequence[str] = DEFAULT_FAN_NAMES,
    ) -> None:
        self._root = root
        self._zone_re = re.compile(zone_pattern, re.IGNORECASE)
        self._fan_names = tuple(fan_names)

    def read(self) -> Telemetry:
        temps = sorted(self._zone_temps(), reverse=True)
        top = temps[:HOTTEST_ZONES_AVERAGED]
        curve_temp = round(sum(top) / len(top), 1) if top else None
        hottest = round(temps[0], 1) if temps else None
        pwm, rpm = self._fan()
        return Telemetry(curve_temp_c=curve_temp, hottest_c=hottest, fan_pwm=pwm, fan_rpm=rpm)

    def _zone_temps(self) -> List[float]:
        values: List[float] = []
        for zone in glob.glob(under(self._root, "/sys/class/thermal/thermal_zone*")):
            kind = _read(os.path.join(zone, "type"))
            if not kind or not self._zone_re.search(kind):
                continue
            raw = _read_int(os.path.join(zone, "temp"))
            if raw is None:
                continue
            celsius = raw / 1000.0
            if _SANE_RANGE_C[0] < celsius < _SANE_RANGE_C[1]:
                values.append(celsius)
        return values

    def _fan(self):
        for hwmon in sorted(glob.glob(under(self._root, "/sys/class/hwmon/hwmon*"))):
            if _read(os.path.join(hwmon, "name")) in self._fan_names:
                return _read_int(os.path.join(hwmon, "pwm1")), _read_int(os.path.join(hwmon, "fan1_input"))
        return None, None


def _read(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().strip()
    except OSError:
        return None


def _read_int(path: str) -> Optional[int]:
    text = _read(path)
    try:
        return int(text) if text is not None else None
    except ValueError:
        return None
