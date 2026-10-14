import unittest

from handheld_fan_tweaker.application import ADOPTED_MANUAL_EDIT, NOTHING_TO_DO, REAPPLIED, FanCurveService
from handheld_fan_tweaker.domain import (
    BackendInfo,
    FanCurve,
    InvalidCurve,
    NoFactoryCurve,
    NotEditable,
    Snapshot,
    Telemetry,
    UnknownProfile,
)

PROFILES = ("silent", "balanced", "turbo")
FACTORY_SILENT = [[50, 0], [70, 80], [92, 255]]
USER_SILENT = [[55, 0], [75, 90], [90, 255]]


class MemoryRepo:
    def __init__(self, curves):
        self.curves = {k: FanCurve.from_pairs(v, validate=False) for k, v in curves.items()}
        self.writes = []

    def read_all(self):
        return dict(self.curves)

    def write(self, profile, curve):
        self.curves[profile] = curve
        self.writes.append(profile)


class FakeDaemon:
    def __init__(self, profile="balanced"):
        self.reloads = 0
        self.profile = profile

    def reload(self):
        self.reloads += 1

    def active_profile(self):
        return self.profile


class FixedTelemetry:
    def read(self):
        return Telemetry(curve_temp_c=61.5, hottest_c=66.0, fan_pwm=90, fan_rpm=None)


class MemorySnapshots:
    def __init__(self, snapshot=None):
        self.snapshot = snapshot or Snapshot()

    def load(self):
        return Snapshot(factory=dict(self.snapshot.factory), custom=dict(self.snapshot.custom))

    def save(self, snapshot):
        self.snapshot = snapshot


def make(editable=True, curves=None, snapshot=None):
    repo = MemoryRepo(curves if curves is not None else {"silent": FACTORY_SILENT})
    daemon = FakeDaemon()
    snaps = MemorySnapshots(snapshot)
    backend = BackendInfo("odin3d", PROFILES, editable, None if editable else "sin soporte")
    service = FanCurveService(backend, FixedTelemetry(), snaps, repository=repo, daemon=daemon)
    return service, repo, daemon, snaps


class StateTest(unittest.TestCase):
    def test_state_reports_curves_factory_profile_and_telemetry(self):
        service, _, _, snaps = make()
        state = service.state()
        self.assertEqual(state["profiles"], {"silent": FACTORY_SILENT})
        self.assertEqual(state["factory"], {"silent": FACTORY_SILENT})
        self.assertEqual(state["active_profile"], "balanced")
        self.assertEqual(state["telemetry"]["fan_pwm"], 90)
        self.assertEqual(snaps.snapshot.factory["silent"], FACTORY_SILENT)


class SetCurveTest(unittest.TestCase):
    def test_writes_remembers_and_reloads(self):
        service, repo, daemon, snaps = make()
        service.set_curve("silent", USER_SILENT)
        self.assertEqual(repo.curves["silent"].to_pairs(), USER_SILENT)
        self.assertEqual(snaps.snapshot.custom["silent"], USER_SILENT)
        self.assertEqual(snaps.snapshot.factory["silent"], FACTORY_SILENT)
        self.assertEqual(daemon.reloads, 1)

    def test_invalid_curve_changes_nothing(self):
        service, repo, daemon, _ = make()
        with self.assertRaises(InvalidCurve):
            service.set_curve("silent", [[50, 0], [99, 200]])
        self.assertEqual(repo.writes, [])
        self.assertEqual(daemon.reloads, 0)

    def test_unknown_profile(self):
        service, _, _, _ = make()
        with self.assertRaises(UnknownProfile):
            service.set_curve("ultra", USER_SILENT)

    def test_not_editable_backend(self):
        service, repo, _, _ = make(editable=False)
        with self.assertRaises(NotEditable):
            service.set_curve("silent", USER_SILENT)
        self.assertEqual(repo.writes, [])


class ResetCurveTest(unittest.TestCase):
    def test_restores_factory_and_forgets_custom(self):
        service, repo, daemon, snaps = make()
        service.set_curve("silent", USER_SILENT)
        service.reset_curve("silent")
        self.assertEqual(repo.curves["silent"].to_pairs(), FACTORY_SILENT)
        self.assertNotIn("silent", snaps.snapshot.custom)
        self.assertEqual(daemon.reloads, 2)

    def test_without_factory_copy(self):
        service, _, _, _ = make(curves={})
        with self.assertRaises(NoFactoryCurve):
            service.reset_curve("silent")


class ReconcileTest(unittest.TestCase):
    def test_nothing_saved(self):
        service, _, daemon, _ = make()
        self.assertEqual(service.reconcile_on_start(), NOTHING_TO_DO)
        self.assertEqual(daemon.reloads, 0)

    def test_reapplies_after_an_update_restored_the_factory_curve(self):
        snap = Snapshot(factory={"silent": FACTORY_SILENT}, custom={"silent": USER_SILENT})
        service, repo, daemon, _ = make(curves={"silent": FACTORY_SILENT}, snapshot=snap)
        self.assertEqual(service.reconcile_on_start(), REAPPLIED)
        self.assertEqual(repo.curves["silent"].to_pairs(), USER_SILENT)
        self.assertEqual(daemon.reloads, 1)

    def test_respects_a_manual_edit(self):
        manual = [[52, 0], [80, 160], [91, 255]]
        snap = Snapshot(factory={"silent": FACTORY_SILENT}, custom={"silent": USER_SILENT})
        service, repo, daemon, snaps = make(curves={"silent": manual}, snapshot=snap)
        self.assertEqual(service.reconcile_on_start(), ADOPTED_MANUAL_EDIT)
        self.assertEqual(repo.writes, [])
        self.assertEqual(snaps.snapshot.custom["silent"], manual)
        self.assertEqual(daemon.reloads, 0)

    def test_already_in_sync(self):
        snap = Snapshot(factory={"silent": FACTORY_SILENT}, custom={"silent": USER_SILENT})
        service, _, daemon, _ = make(curves={"silent": USER_SILENT}, snapshot=snap)
        self.assertEqual(service.reconcile_on_start(), NOTHING_TO_DO)
        self.assertEqual(daemon.reloads, 0)


if __name__ == "__main__":
    unittest.main()
