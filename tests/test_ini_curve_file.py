import os
import tempfile
import unittest

from handheld_fan_tweaker.domain import FanCurve
from handheld_fan_tweaker.infrastructure import IniCurveFile, format_curve_text, parse_curve_text
from handheld_fan_tweaker.infrastructure.ini_curve_file import BACKUP_SUFFIX

PROFILES = ("silent", "balanced", "turbo")

SAMPLE = """# sample config for the tests
[fan]
enabled = yes

[curves]
# a comment that has to survive
silent = 50:0, 60:40, 80:150, 92:255
balanced = 45:0, 70:110, 90:255

[power]
manage_cpu = yes
"""


class CurveTextTest(unittest.TestCase):
    def test_round_trip(self):
        curve = parse_curve_text(" 50:0 ,60:40,  92:255 ")
        self.assertEqual(format_curve_text(curve), "50:0, 60:40, 92:255")

    def test_garbage_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_curve_text("50-0, 60:40")


class IniCurveFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "device.conf")
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(SAMPLE)
        self.file = IniCurveFile(self.path, PROFILES)

    def tearDown(self):
        self.tmp.cleanup()

    def read_text(self):
        with open(self.path, encoding="utf-8") as fh:
            return fh.read()

    def test_reads_only_known_profiles_in_curves_section(self):
        curves = self.file.read_all()
        self.assertEqual(sorted(curves), ["balanced", "silent"])
        self.assertEqual(curves["silent"].to_pairs()[-1], [92, 255])

    def test_write_replaces_only_that_line(self):
        self.file.write("silent", FanCurve.from_pairs([[55, 0], [75, 120], [90, 255]]))
        text = self.read_text()
        self.assertIn("silent = 55:0, 75:120, 90:255\n", text)
        self.assertIn("# a comment that has to survive", text)
        self.assertIn("balanced = 45:0, 70:110, 90:255", text)
        self.assertIn("[power]\nmanage_cpu = yes", text)

    def test_write_adds_missing_profile_inside_the_section(self):
        self.file.write("turbo", FanCurve.from_pairs([[40, 80], [85, 255]]))
        text = self.read_text()
        self.assertLess(text.index("turbo = 40:80, 85:255"), text.index("[power]"))
        self.assertEqual(self.file.read_all()["turbo"].to_pairs(), [[40, 80], [85, 255]])

    def test_write_creates_section_when_missing(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("[fan]\nenabled = yes")
        self.file.write("silent", FanCurve.from_pairs([[50, 0], [90, 255]]))
        self.assertEqual(self.file.read_all()["silent"].to_pairs(), [[50, 0], [90, 255]])
        self.assertIn("enabled = yes\n", self.read_text())

    def test_backup_is_made_once_with_the_original_content(self):
        self.file.write("silent", FanCurve.from_pairs([[50, 0], [90, 255]]))
        self.file.write("silent", FanCurve.from_pairs([[55, 0], [90, 255]]))
        with open(self.path + BACKUP_SUFFIX, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), SAMPLE)

    def test_missing_file_reads_as_empty(self):
        self.assertEqual(IniCurveFile(os.path.join(self.tmp.name, "nope.conf"), PROFILES).read_all(), {})


if __name__ == "__main__":
    unittest.main()
