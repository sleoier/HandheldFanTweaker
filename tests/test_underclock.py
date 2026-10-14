import os
import tempfile
import unittest

from handheld_fan_tweaker.application import UnderclockService
from handheld_fan_tweaker.domain import Cluster, UnknownLevel
from handheld_fan_tweaker.domain.underclock import cap_for, managed_clusters, plan
from handheld_fan_tweaker.infrastructure import JsonSettingStore, SysfsCpuFreq

# Frequency tables read from an AYN Odin 3 running SteamOS ARM Port.
ODIN3_POLICY0 = Cluster("policy0", "0 1 2 3 4 5", 3532800, (
    384000, 556800, 748800, 960000, 1152000, 1363200, 1555200, 1785600, 1996800,
    2227200, 2400000, 2745600, 2918400, 3072000, 3321600, 3532800))
ODIN3_POLICY6 = Cluster("policy6", "6 7", 4089600, (
    1017600, 1209600, 1401600, 1689600, 1958400, 2246400, 2438400, 2649600,
    2841600, 3072000, 3283200, 3513600, 3801600, 4089600))
ODIN3 = [ODIN3_POLICY0, ODIN3_POLICY6]


class PlanTest(unittest.TestCase):
    def test_odin3_levels(self):
        self.assertEqual(plan("low", ODIN3), {"policy0": 3072000, "policy6": 3513600})
        self.assertEqual(plan("medium", ODIN3), {"policy0": 2745600, "policy6": 3072000})
        self.assertEqual(plan("high", ODIN3), {"policy0": 2227200, "policy6": 2438400})

    def test_off_is_full_speed(self):
        self.assertEqual(plan("off", ODIN3), {"policy0": 3532800, "policy6": 4089600})

    def test_unknown_level(self):
        with self.assertRaises(UnknownLevel):
            plan("ultra", ODIN3)

    def test_little_cores_are_left_alone_with_three_clusters(self):
        little = Cluster("policy0", "0 1", 2016000, (1000000, 2016000))
        mid = Cluster("policy2", "2 3 4", 3000000, (2000000, 3000000))
        prime = Cluster("policy7", "7", 3300000, (2000000, 3300000))
        self.assertEqual([c.name for c in managed_clusters([little, mid, prime])], ["policy2", "policy7"])

    def test_no_step_below_target_uses_the_lowest(self):
        self.assertEqual(cap_for("high", Cluster("p", "0", 1000000, (900000, 1000000))), 900000)


class FakeCpu:
    def __init__(self, clusters):
        self._clusters = clusters
        self.caps = {c.name: c.max_khz for c in clusters}

    def clusters(self):
        return self._clusters

    def current_max(self, cluster):
        return self.caps.get(cluster)

    def set_max(self, cluster, khz):
        self.caps[cluster] = khz


class MemorySettings:
    def __init__(self):
        self.data = {}

    def get(self, key, default):
        return self.data.get(key, default)

    def put(self, key, value):
        self.data[key] = value


class FakeDaemon:
    def __init__(self):
        self.reloads = 0

    def reload(self):
        self.reloads += 1

    def active_profile(self):
        return None


class UnderclockServiceTest(unittest.TestCase):
    def setUp(self):
        self.cpu = FakeCpu(ODIN3)
        self.settings = MemorySettings()
        self.daemon = FakeDaemon()
        self.service = UnderclockService(self.cpu, self.settings, daemon=self.daemon)

    def test_defaults_to_off_and_changes_nothing(self):
        self.assertEqual(self.service.level(), "off")
        self.assertEqual(self.service.enforce(), [])
        self.assertEqual(self.cpu.caps, {"policy0": 3532800, "policy6": 4089600})

    def test_set_level_applies_and_remembers(self):
        self.service.set_level("medium")
        self.assertEqual(self.cpu.caps, {"policy0": 2745600, "policy6": 3072000})
        self.assertEqual(self.settings.data["underclock"], "medium")

    def test_enforce_restores_a_cap_the_daemon_raised(self):
        self.service.set_level("low")
        self.cpu.caps["policy6"] = 4089600
        self.assertEqual(self.service.enforce(), ["policy6"])
        self.assertEqual(self.cpu.caps["policy6"], 3513600)

    def test_enforce_keeps_a_stricter_cap(self):
        self.service.set_level("low")
        self.cpu.caps["policy6"] = 2000000
        self.assertEqual(self.service.enforce(), [])
        self.assertEqual(self.cpu.caps["policy6"], 2000000)

    def test_off_restores_full_speed_and_reloads_the_daemon(self):
        self.service.set_level("high")
        self.service.set_level("off")
        self.assertEqual(self.cpu.caps, {"policy0": 3532800, "policy6": 4089600})
        self.assertEqual(self.daemon.reloads, 1)

    def test_bad_level_changes_nothing(self):
        with self.assertRaises(UnknownLevel):
            self.service.set_level("ultra")
        self.assertEqual(self.settings.data, {})

    def test_state_lists_targets(self):
        self.service.set_level("high")
        state = self.service.state()
        self.assertEqual(state["level"], "high")
        self.assertEqual([c["target_khz"] for c in state["clusters"]], [2227200, 2438400])


class SysfsAndSettingsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        for c in ODIN3:
            d = os.path.join(self.root, "sys/devices/system/cpu/cpufreq", c.name)
            os.makedirs(d)
            files = {
                "cpuinfo_max_freq": c.max_khz,
                "related_cpus": c.cpus,
                "scaling_available_frequencies": " ".join(map(str, c.available_khz)),
                "scaling_max_freq": c.max_khz,
            }
            for name, value in files.items():
                with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                    fh.write(f"{value}\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_clusters_and_writes_caps(self):
        cpu = SysfsCpuFreq(root=self.root)
        self.assertEqual(cpu.clusters(), ODIN3)
        cpu.set_max("policy6", 3072000)
        self.assertEqual(cpu.current_max("policy6"), 3072000)

    def test_refuses_paths_that_are_not_policies(self):
        with self.assertRaises(ValueError):
            SysfsCpuFreq(root=self.root).set_max("../../evil", 1)

    def test_settings_survive_a_new_instance(self):
        settings_dir = os.path.join(self.root, "settings")
        JsonSettingStore(settings_dir).put("underclock", "low")
        self.assertEqual(JsonSettingStore(settings_dir).get("underclock", "off"), "low")


if __name__ == "__main__":
    unittest.main()
