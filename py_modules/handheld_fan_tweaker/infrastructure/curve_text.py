"""Curve format used by the daemons' config files: "48:0, 55:30, 65:55"."""
from __future__ import annotations

from typing import List

from ..domain import FanCurve


def parse_curve_text(text: str) -> FanCurve:
    pairs: List[List[int]] = []
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        temp, sep, pwm = chunk.partition(":")
        if not sep:
            raise ValueError(f"point without ':' → {chunk!r}")
        pairs.append([int(temp.strip()), int(pwm.strip())])
    if not pairs:
        raise ValueError("empty curve")
    return FanCurve.from_pairs(pairs, validate=False)


def format_curve_text(curve: FanCurve) -> str:
    return ", ".join(f"{p.temp_c}:{p.pwm}" for p in curve.points)
