from __future__ import annotations

from typing import Dict, Optional, Sequence

from ..domain import (
    BackendInfo,
    FanCurve,
    NoFactoryCurve,
    NotEditable,
    Pairs,
    Snapshot,
    UnknownProfile,
    limits,
)
from ..ports import CurveRepository, DaemonController, SnapshotStore, TelemetrySource

NOTHING_TO_DO = "nothing-to-do"
REAPPLIED = "reapplied"
ADOPTED_MANUAL_EDIT = "adopted-manual-edit"


class FanCurveService:
    def __init__(
        self,
        backend: BackendInfo,
        telemetry: TelemetrySource,
        snapshots: SnapshotStore,
        repository: Optional[CurveRepository] = None,
        daemon: Optional[DaemonController] = None,
    ) -> None:
        self._backend = backend
        self._telemetry = telemetry
        self._snapshots = snapshots
        self._repo = repository
        self._daemon = daemon

    def state(self) -> dict:
        curves: Dict[str, Pairs] = {}
        factory: Dict[str, Pairs] = {}
        if self._repo is not None:
            current = self._repo.read_all()
            snapshot = self._remember_factory(current)
            curves = {name: current[name].to_pairs() for name in self._backend.profiles if name in current}
            factory = {name: snapshot.factory[name] for name in self._backend.profiles if name in snapshot.factory}
        return {
            "backend": self._backend.name,
            "editable": self._backend.editable,
            "reason": self._backend.reason,
            "profile_order": list(self._backend.profiles),
            "profiles": curves,
            "factory": factory,
            "active_profile": self._daemon.active_profile() if self._daemon else None,
            "telemetry": self._telemetry.read().as_dict(),
            "limits": limits(),
        }

    def telemetry(self) -> dict:
        return self._telemetry.read().as_dict()

    def set_curve(self, profile: str, pairs: Sequence[Sequence[int]]) -> Pairs:
        repo, daemon = self._require_editable(profile)
        curve = FanCurve.from_pairs(pairs)
        snapshot = self._remember_factory(repo.read_all())
        repo.write(profile, curve)
        snapshot.custom[profile] = curve.to_pairs()
        self._snapshots.save(snapshot)
        daemon.reload()
        return curve.to_pairs()

    def reset_curve(self, profile: str) -> Pairs:
        repo, daemon = self._require_editable(profile)
        snapshot = self._remember_factory(repo.read_all())
        original = snapshot.factory.get(profile)
        if not original:
            raise NoFactoryCurve(f"there's no saved original curve for '{profile}'")
        curve = FanCurve.from_pairs(original, validate=False)
        repo.write(profile, curve)
        snapshot.custom.pop(profile, None)
        self._snapshots.save(snapshot)
        daemon.reload()
        return curve.to_pairs()

    def reconcile_on_start(self) -> str:
        """If the config went back to the factory curve (a system update), write
        the user's curve again. If someone hand-edited it to something else,
        keep that edit as the user's curve."""
        if not self._backend.editable or self._repo is None or self._daemon is None:
            return NOTHING_TO_DO
        snapshot = self._snapshots.load()
        if not snapshot.custom:
            return NOTHING_TO_DO
        current = self._repo.read_all()
        reapplied = adopted = False
        for profile, wanted in list(snapshot.custom.items()):
            if profile not in self._backend.profiles:
                continue
            now = current.get(profile)
            now_pairs = now.to_pairs() if now else None
            if now_pairs == wanted:
                continue
            if now_pairs is None or now_pairs == snapshot.factory.get(profile):
                self._repo.write(profile, FanCurve.from_pairs(wanted))
                reapplied = True
            else:
                snapshot.custom[profile] = now_pairs
                adopted = True
        if reapplied or adopted:
            self._snapshots.save(snapshot)
        if reapplied:
            self._daemon.reload()
            return REAPPLIED
        return ADOPTED_MANUAL_EDIT if adopted else NOTHING_TO_DO

    def _require_editable(self, profile: str):
        if not self._backend.editable or self._repo is None or self._daemon is None:
            raise NotEditable(self._backend.reason or "this device doesn't allow editing fan curves")
        if profile not in self._backend.profiles:
            raise UnknownProfile(f"unknown profile '{profile}'; available: {', '.join(self._backend.profiles)}")
        return self._repo, self._daemon

    def _remember_factory(self, current: Dict[str, FanCurve]) -> Snapshot:
        snapshot = self._snapshots.load()
        changed = False
        for name in self._backend.profiles:
            if name in current and name not in snapshot.factory:
                snapshot.factory[name] = current[name].to_pairs()
                changed = True
        if changed:
            self._snapshots.save(snapshot)
        return snapshot
