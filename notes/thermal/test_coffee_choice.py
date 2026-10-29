"""Check the coffee-choice model against the recorded example and invariants."""

import unittest

from coffee_choice import Parameters, compare, cool, mix


class CoffeeChoiceTests(unittest.TestCase):
    def test_recorded_default_and_warm_creamer(self):
        early, late = compare(Parameters())
        self.assertAlmostEqual(early, 33.05, places=2)
        self.assertAlmostEqual(late, 31.57, places=2)
        self.assertAlmostEqual(late - early, -1.49, places=2)
        early, late = compare(Parameters(creamer_c=70.0))
        self.assertAlmostEqual(early, 34.44, places=2)
        self.assertAlmostEqual(late, 34.58, places=2)
        self.assertAlmostEqual(late - early, 0.14, places=2)

    def test_instant_addition_gives_equal_results(self):
        early, late = compare(Parameters(add_later_s=0.0))
        self.assertAlmostEqual(early, late)

    def test_cooling_and_mixing_obey_model(self):
        self.assertAlmostEqual(cool(90, 20, 1045, 3, 0), 90)
        self.assertAlmostEqual(mix(80, 20, 4, 1), 68)
        with self.assertRaises(ValueError):
            compare(Parameters(add_later_s=601))


if __name__ == "__main__":
    unittest.main()
