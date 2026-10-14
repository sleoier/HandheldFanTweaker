from __future__ import annotations

from typing import Dict, List, Optional

from ..domain import LEVELS, OFF
from ..domain.underclock import check_level, managed_clusters, plan
from ..ports import CpuFrequencyControl, DaemonController, SettingStore

SETTING_KEY = "underclock"


class UnderclockService:
    def __init__(
        self,
        cpu: CpuFrequencyControl,
        settings: SettingStore,
        daemon: Optional[DaemonController] = None,
    ) -> None:
        self._cpu = cpu
        self._settings = settings
        self._daemon = daemon

    def level(self) -> str:
        level = self._settings.get(SETTING_KEY, OFF)
        return level if level in LEVELS else OFF

    def state(self) -> dict:
        level = self.level()
        clusters = managed_clusters(self._cpu.clusters())
        caps = plan(level, clusters)
        return {
            "level": level,
            "levels": list(LEVELS),
            "clusters": [
                {
                    "name": c.name,
                    "cpus": c.cpus,
                    "max_khz": c.max_khz,
                    "target_khz": caps[c.name],
                    "current_max_khz": self._cpu.current_max(c.name),
                }
                for c in clusters
            ],
        }

    def set_level(self, level: str) -> dict:
        check_level(level)
        self._settings.put(SETTING_KEY, level)
        if level == OFF:
            self._release()
        else:
            self.enforce()
        return self.state()

    def enforce(self) -> List[str]:
        """Lowers any cluster whose cap is above the chosen level. A lower
        cap (for example Steam's TDP limit) is left alone, so the stricter
        limit always wins. Returns the clusters that were changed."""
        level = self.level()
        if level == OFF:
            return []
        changed = []
        for name, cap in plan(level, self._cpu.clusters()).items():
            current = self._cpu.current_max(name)
            if current is None or current > cap:
                self._cpu.set_max(name, cap)
                changed.append(name)
        return changed

    def _release(self) -> None:
        for name, top in self._tops().items():
            self._cpu.set_max(name, top)
        if self._daemon is not None:
            self._daemon.reload()  # lets the daemon put its own TDP caps back

    def _tops(self) -> Dict[str, int]:
        return {c.name: c.max_khz for c in managed_clusters(self._cpu.clusters())}
