import json
import os
import tempfile
import unittest

from handheld_fan_tweaker.composition import build_service
from handheld_fan_tweaker.infrastructure import KONKRD, ODIN3D, SysfsTelemetry, SystemdDaemon, curves_support, detect


def put(root, path, text=""):
    full = os.path.join(root, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)
    return full


class DetectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_nothing_installed(self):
        self.assertIsNone(detect(self.root))

    def test_odin3d(self):
        put(self.root, ODIN3D.executable, "#!/usr/bin/env python3\n")
        self.assertEqual(detect(self.root), ODIN3D)
        self.assertEqual(curves_support(ODIN3D, self.root), (True, None))

    def test_konkrd_without_conf_curves_is_read_only(self):
        put(self.root, KONKRD.executable, "FAN = {'silent': []}\n")
        editable, reason = curves_support(KONKRD, self.root)
        self.assertFalse(editable)
        self.assertIn("konkrd", reason)

    def test_konkrd_that_reads_conf_curves(self):
        put(self.root, KONKRD.executable, 'cp.get("curves", name)\n')
        self.assertEqual(curves_support(KONKRD, self.root), (True, None))

    def test_active_profile_from_state_file(self):
        put(self.root, ODIN3D.state_file, json.dumps({"profile": "turbo"}))
        self.assertEqual(SystemdDaemon(ODIN3D, root=self.root).active_profile(), "turbo")

    def test_reload_sends_sighup_to_the_unit(self):
        calls = []
        SystemdDaemon(ODIN3D, root=self.root, runner=calls.append).reload()
        self.assertEqual(calls, [["systemctl", "kill", "--signal=HUP", "odin3d.service"]])


class TelemetryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        zones = [("cpu-0-0", 70000), ("cpu-1-0", 60000), ("gpu-0", 80000), ("battery", 99000), ("cpu-2-0", 50000)]
        for i, (kind, milli) in enumerate(zones):
            put(self.root, f"/sys/class/thermal/thermal_zone{i}/type", kind + "\n")
            put(self.root, f"/sys/class/thermal/thermal_zone{i}/temp", f"{milli}\n")
        put(self.root, "/sys/class/hwmon/hwmon3/name", "pwmfan\n")
        put(self.root, "/sys/class/hwmon/hwmon3/pwm1", "128\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_averages_the_three_hottest_cpu_gpu_zones(self):
        t = SysfsTelemetry(root=self.root).read()
        self.assertEqual(t.curve_temp_c, 70.0)  # (80 + 70 + 60) / 3; the battery zone is ignored
        self.assertEqual(t.hottest_c, 80.0)
        self.assertEqual(t.fan_pwm, 128)
        self.assertIsNone(t.fan_rpm)


class CompositionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "root")
        self.settings = os.path.join(self.tmp.name, "settings")

    def tearDown(self):
        self.tmp.cleanup()

    def test_end_to_end_on_a_fake_odin3(self):
        put(self.root, ODIN3D.executable, "")
        conf = put(self.root, ODIN3D.config, "[curves]\nsilent = 50:0, 70:80, 92:255\n")
        service = build_service(self.settings, fs_root=self.root, sys_root=self.root, dry_run=True)
        state = service.state()
        self.assertTrue(state["editable"])
        self.assertEqual(state["backend"], "odin3d")
        service.set_curve("silent", [[55, 0], [75, 90], [90, 255]])
        with open(conf, encoding="utf-8") as fh:
            self.assertIn("silent = 55:0, 75:90, 90:255", fh.read())
        service.reset_curve("silent")
        with open(conf, encoding="utf-8") as fh:
            self.assertIn("silent = 50:0, 70:80, 92:255", fh.read())

    def test_snapshot_file_is_readable_by_everyone(self):
        put(self.root, ODIN3D.executable, "")
        put(self.root, ODIN3D.config, "[curves]\nsilent = 50:0, 70:80, 92:255\n")
        build_service(self.settings, fs_root=self.root, sys_root=self.root, dry_run=True).state()
        mode = os.stat(os.path.join(self.settings, "curves.json")).st_mode & 0o777
        self.assertEqual(mode, 0o644)

    def test_no_daemon_is_not_editable(self):
        state = build_service(self.settings, fs_root=self.root, sys_root=self.root).state()
        self.assertFalse(state["editable"])
        self.assertIsNone(state["backend"])


if __name__ == "__main__":
    unittest.main()
