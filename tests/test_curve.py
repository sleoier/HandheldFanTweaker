import unittest

from handheld_fan_tweaker.domain import FanCurve, InvalidCurve


class FanCurveValidationTest(unittest.TestCase):
    def test_accepts_a_sane_curve(self):
        curve = FanCurve.from_pairs([[45, 0], [60, 80], [80, 180], [90, 255]])
        self.assertEqual(curve.to_pairs(), [[45, 0], [60, 80], [80, 180], [90, 255]])

    def test_rejects_too_few_points(self):
        with self.assertRaises(InvalidCurve):
            FanCurve.from_pairs([[90, 255]])

    def test_rejects_temperatures_out_of_order(self):
        with self.assertRaises(InvalidCurve):
            FanCurve.from_pairs([[60, 0], [50, 100], [90, 255]])

    def test_rejects_speed_going_down(self):
        with self.assertRaises(InvalidCurve):
            FanCurve.from_pairs([[40, 100], [60, 50], [90, 255]])

    def test_rejects_curve_that_never_reaches_full_speed_in_time(self):
        with self.assertRaises(InvalidCurve):
            FanCurve.from_pairs([[40, 0], [90, 200], [100, 255]])

    def test_rejects_pwm_out_of_range(self):
        with self.assertRaises(InvalidCurve):
            FanCurve.from_pairs([[40, 0], [90, 300]])

    def test_rejects_non_numeric_points(self):
        with self.assertRaises(InvalidCurve):
            FanCurve.from_pairs([["a", 0], [90, 255]])

    def test_lenient_mode_keeps_system_curves_as_they_are(self):
        curve = FanCurve.from_pairs([[40, 70], [86, 200]], validate=False)
        self.assertEqual(len(curve.points), 2)


class FanCurveInterpolationTest(unittest.TestCase):
    def setUp(self):
        self.curve = FanCurve.from_pairs([[50, 0], [70, 100], [90, 255]])

    def test_below_first_point_uses_first_value(self):
        self.assertEqual(self.curve.pwm_at(30), 0)

    def test_on_a_point(self):
        self.assertEqual(self.curve.pwm_at(70), 100)

    def test_between_points_is_linear(self):
        self.assertEqual(self.curve.pwm_at(60), 50)

    def test_above_last_point_uses_last_value(self):
        self.assertEqual(self.curve.pwm_at(105), 255)


if __name__ == "__main__":
    unittest.main()
