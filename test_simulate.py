"""Checks for physical invariants, delay semantics and deterministic results."""
import json
import math
import unittest
from simulate import ROOT, State, DelayLine, advance, pure_pursuit, run_case, validate


class SimulationChecks(unittest.TestCase):
    def test_straight_motion_matches_analytic_solution(self):
        state = State(0, 0, 0)
        for _ in range(100):
            state = advance(state, 0, 2, 0.5, 0.01)
        self.assertAlmostEqual(state.x, 2)
        self.assertEqual(state.y, 0)
        self.assertEqual(state.yaw, 0)

    def test_delay_impulse_and_zero_delay(self):
        delayed = DelayLine(3)
        self.assertEqual([delayed.push(x) for x in [1, 0, 0, 0, 0]], [0, 0, 0, 1, 0])
        instant = DelayLine(0)
        self.assertEqual([instant.push(x) for x in [1, 2, 3]], [1, 2, 3])

    def test_controller_turns_toward_path(self):
        self.assertLess(pure_pursuit(State(0, 0.5, 0), (1, 0), 0.5, 0.6), 0)
        self.assertEqual(pure_pursuit(State(0, 0, 0), (1, 0), 0.5, 0.6), 0)

    def test_straight_equilibrium_and_repeatability(self):
        config = json.loads((ROOT/"config.json").read_text())
        config["initial_lateral_offset"] = 0
        rows, summary = run_case(config, "straight", 0.2)
        self.assertTrue(summary["completed"])
        self.assertAlmostEqual(summary["rmse_m"], 0, places=12)
        self.assertEqual((rows, summary), run_case(config, "straight", 0.2))

    def test_fractional_step_delay_is_rejected(self):
        config = json.loads((ROOT/"config.json").read_text())
        config["delays"] = [0.015]
        with self.assertRaises(ValueError):
            validate(config)


if __name__ == "__main__":
    unittest.main()
