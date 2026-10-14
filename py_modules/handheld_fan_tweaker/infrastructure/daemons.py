from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

DEFAULT_PROFILES = ("silent", "balanced", "turbo")


@dataclass(frozen=True)
class DaemonSpec:
    name: str
    unit: str
    executable: str
    config: str
    state_file: str
    profiles: Tuple[str, ...] = DEFAULT_PROFILES
    # When False, support is detected by looking at the daemon's source.
    reads_conf_curves: bool = False


ODIN3D = DaemonSpec(
    name="odin3d",
    unit="odin3d.service",
    executable="/usr/lib/odin3/odin3d",
    config="/etc/odin3.conf",
    state_file="/var/lib/odin3/state.json",
    reads_conf_curves=True,
)

KONKRD = DaemonSpec(
    name="konkrd",
    unit="konkrd.service",
    executable="/usr/lib/konkr/konkrd",
    config="/etc/konkrd.conf",
    state_file="/var/lib/konkrd/state.json",
)

KNOWN_DAEMONS: Sequence[DaemonSpec] = (ODIN3D, KONKRD)


def under(root: str, path: str) -> str:
    return os.path.join(root, path.lstrip("/"))


def detect(root: str = "/") -> Optional[DaemonSpec]:
    for spec in KNOWN_DAEMONS:
        if os.path.exists(under(root, spec.executable)):
            return spec
    return None


def curves_support(spec: DaemonSpec, root: str = "/") -> Tuple[bool, Optional[str]]:
    if spec.reads_conf_curves:
        return True, None
    try:
        with open(under(root, spec.executable), encoding="utf-8", errors="replace") as fh:
            source = fh.read()
    except OSError:
        return False, f"couldn't read {spec.executable}"
    # Both daemons are Python scripts; one that reads the section names it.
    if '"curves"' in source or "'curves'" in source:
        return True, None
    return False, (
        f"{spec.name} doesn't read fan curves from {spec.config} yet; "
        "on this device the curves are built into the daemon"
    )


Runner = Callable[[Sequence[str]], None]


def _run(cmd: Sequence[str]) -> None:
    subprocess.run(list(cmd), check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)


class SystemdDaemon:
    def __init__(self, spec: DaemonSpec, root: str = "/", runner: Runner = _run) -> None:
        self._spec = spec
        self._root = root
        self._runner = runner

    def reload(self) -> None:
        self._runner(["systemctl", "kill", "--signal=HUP", self._spec.unit])

    def active_profile(self) -> Optional[str]:
        try:
            with open(under(self._root, self._spec.state_file), encoding="utf-8") as fh:
                profile = json.load(fh).get("profile")
        except (OSError, ValueError, AttributeError):
            return None
        return profile if profile in self._spec.profiles else None


class DryRunDaemon(SystemdDaemon):
    def reload(self) -> None:
        return None
