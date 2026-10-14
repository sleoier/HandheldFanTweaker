from __future__ import annotations

import glob
import os
from typing import List, Optional

from ..domain import Cluster
from .daemons import under

POLICY_GLOB = "/sys/devices/system/cpu/cpufreq/policy*"


class SysfsCpuFreq:
    def __init__(self, root: str = "/") -> None:
        self._root = root

    def clusters(self) -> List[Cluster]:
        found = []
        for path in sorted(glob.glob(under(self._root, POLICY_GLOB))):
            top = _read_int(os.path.join(path, "cpuinfo_max_freq"))
            if not top:
                continue
            steps = tuple(sorted(int(f) for f in (_read(os.path.join(path, "scaling_available_frequencies")) or "").split() if f.isdigit()))
            found.append(Cluster(
                name=os.path.basename(path),
                cpus=_read(os.path.join(path, "related_cpus")) or "",
                max_khz=top,
                available_khz=steps,
            ))
        return found

    def current_max(self, cluster: str) -> Optional[int]:
        return _read_int(self._file(cluster))

    def set_max(self, cluster: str, khz: int) -> None:
        with open(self._file(cluster), "w", encoding="utf-8") as fh:
            fh.write(str(int(khz)))

    def _file(self, cluster: str) -> str:
        if not cluster.startswith("policy") or not cluster[6:].isdigit():
            raise ValueError(f"not a cpufreq policy: {cluster!r}")
        return under(self._root, f"/sys/devices/system/cpu/cpufreq/{cluster}/scaling_max_freq")


def _read(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return None


def _read_int(path: str) -> Optional[int]:
    text = _read(path)
    try:
        return int(text) if text else None
    except ValueError:
        return None
