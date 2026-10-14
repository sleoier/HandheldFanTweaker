"""Edits the [curves] section of a config file line by line.

configparser would rewrite the whole file and drop its comments, so only the
`profile = ...` lines inside [curves] are touched here.
"""
from __future__ import annotations

import os
import re
import shutil
import tempfile
from typing import Dict, List, Optional, Sequence, Tuple

from ..domain import FanCurve
from .curve_text import format_curve_text, parse_curve_text

SECTION = "curves"
BACKUP_SUFFIX = ".handheldfantweaker.bak"

_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*=\s*(.*?)\s*$")


class IniCurveFile:
    def __init__(self, path: str, profiles: Sequence[str]) -> None:
        self._path = path
        self._profiles = tuple(profiles)

    def read_all(self) -> Dict[str, FanCurve]:
        curves: Dict[str, FanCurve] = {}
        lines = self._read_lines()
        start, end = _section_bounds(lines, SECTION)
        if start is None:
            return curves
        for line in lines[start + 1:end]:
            key, value = _key_value(line)
            if key in self._profiles:
                try:
                    curves[key] = parse_curve_text(value)
                except ValueError:
                    continue
        return curves

    def write(self, profile: str, curve: FanCurve) -> None:
        lines = self._read_lines()
        new_line = f"{profile} = {format_curve_text(curve)}\n"
        start, end = _section_bounds(lines, SECTION)
        if start is None:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines += ["\n", f"[{SECTION}]\n", new_line]
        else:
            for i in range(start + 1, end):
                if _key_value(lines[i])[0] == profile:
                    lines[i] = new_line
                    break
            else:
                insert_at = end
                while insert_at > start + 1 and not lines[insert_at - 1].strip():
                    insert_at -= 1
                lines.insert(insert_at, new_line)
        self._backup_once()
        self._atomic_write("".join(lines))

    def _read_lines(self) -> List[str]:
        try:
            with open(self._path, encoding="utf-8") as fh:
                return fh.readlines()
        except FileNotFoundError:
            return []

    def _backup_once(self) -> None:
        backup = self._path + BACKUP_SUFFIX
        if os.path.exists(self._path) and not os.path.exists(backup):
            shutil.copy2(self._path, backup)

    def _atomic_write(self, text: str) -> None:
        directory = os.path.dirname(self._path) or "."
        mode = os.stat(self._path).st_mode & 0o777 if os.path.exists(self._path) else 0o644
        fd, tmp = tempfile.mkstemp(prefix=".hft-", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.chmod(tmp, mode)
            os.replace(tmp, self._path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise


def _section_bounds(lines: List[str], name: str) -> Tuple[Optional[int], int]:
    start = None
    for i, line in enumerate(lines):
        match = _SECTION_RE.match(line)
        if not match:
            continue
        if start is not None:
            return start, i
        if match.group(1).strip().lower() == name:
            start = i
    return start, len(lines)


def _key_value(line: str) -> Tuple[Optional[str], str]:
    stripped = line.lstrip()
    if not stripped or stripped[0] in "#;":
        return None, ""
    match = _KEY_RE.match(line)
    if not match:
        return None, ""
    return match.group(1), match.group(2)
