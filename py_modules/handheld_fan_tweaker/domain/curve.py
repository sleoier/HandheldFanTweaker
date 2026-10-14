from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .errors import InvalidCurve

PWM_MAX = 255
MIN_POINTS = 2
MAX_POINTS = 10
TEMP_MIN_C = 20
TEMP_MAX_C = 110
# Second safety net on top of the daemon's own critical-temperature override.
FULL_SPEED_BY_C = 95


@dataclass(frozen=True)
class CurvePoint:
    temp_c: int
    pwm: int


@dataclass(frozen=True)
class FanCurve:
    points: Tuple[CurvePoint, ...]

    @classmethod
    def from_pairs(cls, pairs: Iterable[Sequence[int]], *, validate: bool = True) -> "FanCurve":
        """validate=False is for curves read from the system config, which we
        accept as they are."""
        try:
            points = tuple(CurvePoint(int(t), int(p)) for t, p in pairs)
        except (TypeError, ValueError) as exc:
            raise InvalidCurve("every point has to be [temperature, pwm] with whole numbers") from exc
        curve = cls(points)
        if validate:
            curve.validate()
        return curve

    def validate(self) -> None:
        count = len(self.points)
        if not MIN_POINTS <= count <= MAX_POINTS:
            raise InvalidCurve(f"a curve needs between {MIN_POINTS} and {MAX_POINTS} points (this one has {count})")
        for point in self.points:
            if not TEMP_MIN_C <= point.temp_c <= TEMP_MAX_C:
                raise InvalidCurve(f"{point.temp_c} °C is outside the {TEMP_MIN_C}-{TEMP_MAX_C} °C range")
            if not 0 <= point.pwm <= PWM_MAX:
                raise InvalidCurve(f"PWM {point.pwm} is outside the 0-{PWM_MAX} range")
        for prev, cur in zip(self.points, self.points[1:]):
            if cur.temp_c <= prev.temp_c:
                raise InvalidCurve("temperatures have to go from low to high, without repeats")
            if cur.pwm < prev.pwm:
                raise InvalidCurve(f"fan speed can't drop as the temperature rises ({prev.temp_c} → {cur.temp_c} °C)")
        if not any(p.pwm == PWM_MAX and p.temp_c <= FULL_SPEED_BY_C for p in self.points):
            raise InvalidCurve(f"the curve has to reach 100 % (PWM {PWM_MAX}) at {FULL_SPEED_BY_C} °C or lower")

    def pwm_at(self, temp_c: float) -> int:
        pts = self.points
        if not pts:
            return 0
        if temp_c <= pts[0].temp_c:
            return pts[0].pwm
        for lo, hi in zip(pts, pts[1:]):
            if temp_c <= hi.temp_c:
                span = hi.temp_c - lo.temp_c
                ratio = (temp_c - lo.temp_c) / span if span else 1.0
                return round(lo.pwm + ratio * (hi.pwm - lo.pwm))
        return pts[-1].pwm

    def to_pairs(self) -> List[List[int]]:
        return [[p.temp_c, p.pwm] for p in self.points]


def limits() -> dict:
    return {
        "pwm_max": PWM_MAX,
        "min_points": MIN_POINTS,
        "max_points": MAX_POINTS,
        "temp_min_c": TEMP_MIN_C,
        "temp_max_c": TEMP_MAX_C,
        "full_speed_by_c": FULL_SPEED_BY_C,
    }
