from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

from .errors import FanCurvesError

OFF = "off"
LEVELS: Tuple[str, ...] = (OFF, "low", "medium", "high")

# Share of each cluster's top clock. On the Odin 3 these land on
# 3072/3513.6, 2745.6/3072 and 2227.2/2438.4 MHz, just below the points where
# the kernel's energy model shows power climbing much faster than clock.
LEVEL_RATIO: Dict[str, float] = {"low": 0.87, "medium": 0.78, "high": 0.64}


class UnknownLevel(FanCurvesError):
    pass


@dataclass(frozen=True)
class Cluster:
    name: str
    cpus: str
    max_khz: int
    available_khz: Tuple[int, ...]


def check_level(level: str) -> str:
    if level not in LEVELS:
        raise UnknownLevel(f"unknown underclock level '{level}'; available: {', '.join(LEVELS)}")
    return level


def managed_clusters(clusters: Sequence[Cluster]) -> Tuple[Cluster, ...]:
    """With three or more clusters the slowest one is little cores, which
    draw too little to be worth capping."""
    if len(clusters) < 3:
        return tuple(clusters)
    slowest = min(c.max_khz for c in clusters)
    return tuple(c for c in clusters if c.max_khz > slowest)


def cap_for(level: str, cluster: Cluster) -> int:
    if check_level(level) == OFF:
        return cluster.max_khz
    target = cluster.max_khz * LEVEL_RATIO[level]
    steps = sorted(cluster.available_khz) or [cluster.max_khz]
    below = [f for f in steps if f <= target]
    return below[-1] if below else steps[0]


def plan(level: str, clusters: Sequence[Cluster]) -> Dict[str, int]:
    return {c.name: cap_for(level, c) for c in managed_clusters(clusters)}
