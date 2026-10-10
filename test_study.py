import json
import math
import unittest
from simulate import ROOT, State, advance, predict_state, pure_pursuit, run_case
from study import make_cases, prediction_residual

try:
    import numpy as np
    from linear_analysis import augmented_matrix, continuous_delay_margin, spectral_radius
except ImportError:
    np = None


class PredictorChecks(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/"config.json").read_text())
        self.config["integrator"] = "exact"

    def test_exact_step_matches_circle(self):
        dt, speed, wheelbase, steering = 0.7, 1.3, 0.5, 0.3
        rate = speed/wheelbase*math.tan(steering)
        state = advance(State(0, 0, 0), steering, speed, wheelbase, dt, "exact")
        self.assertAlmostEqual(state.x, speed/rate*math.sin(rate*dt))
        self.assertAlmostEqual(state.y, speed/rate*(1-math.cos(rate*dt)))
        self.assertAlmostEqual(state.yaw, rate*dt)

    def test_exact_composition_for_constant_input(self):
        a = advance(State(1, 2, 0.3), 0.2, 1, 0.5, 0.4, "exact")
        b = advance(advance(State(1, 2, 0.3), 0.2, 1, 0.5, 0.2, "exact"), 0.2, 1, 0.5, 0.2, "exact")
        for key in ("x", "y", "yaw"):
            self.assertAlmostEqual(getattr(a, key), getattr(b, key))

    def test_prediction_does_not_mutate_state_or_history(self):
        state = State(1, 2, 0.3)
        pending = [0.1, 0.2]
        predict_state(state, pending, 1, 0.5, 0.02)
        self.assertEqual(state, State(1, 2, 0.3))
        self.assertEqual(pending, [0.1, 0.2])

    def test_zero_delay_equals_baseline(self):
        original, score = run_case(self.config, "s_curve", 0)
        predicted, predicted_score = run_case(self.config, "s_curve", 0, "predictor")
        self.assertEqual(score, predicted_score)
        for a, b in zip(original, predicted):
            self.assertEqual(a, {key: b[key] for key in a})

    def test_matched_prediction_matches_future_plant(self):
        rows, _ = run_case(self.config, "s_curve", 0.8, "predictor")
        self.assertLess(prediction_residual(rows, 40), 1e-10)

    def test_delay_mismatch_has_prediction_error(self):
        rows, _ = run_case(self.config, "s_curve", 0.8, "predictor", estimated_delay=0.4)
        self.assertGreater(prediction_residual(rows, 20), 0.01)

    def test_study_has_disjoint_development_and_holdout(self):
        plan = json.loads((ROOT/"study_config.json").read_text())
        self.assertFalse(set(plan["development_routes"]) & set(plan["holdout_routes"]))
        cases = make_cases(plan)
        for case in cases:
            if case["group"] == "lookahead":
                self.assertNotIn(case["route"], plan["holdout_routes"])


@unittest.skipIf(np is None, "NumPy is needed for linear-model checks")
class LinearModelChecks(unittest.TestCase):
    def test_predicted_poles_equal_no_delay_poles(self):
        reference = spectral_radius(augmented_matrix(1, 0.5, 1, 0.02, 0))
        for steps in (1, 10, 40):
            self.assertAlmostEqual(reference, spectral_radius(augmented_matrix(1, 0.5, 1, 0.02, steps, "predictor")), places=8)

    def test_matrix_matches_nonlinear_small_perturbation(self):
        for controller in ("pp", "predictor"):
            n, dt, eps = 3, 0.02, 1e-6
            matrix = augmented_matrix(1, 0.5, 1, dt, n, controller)
            def nonlinear(z):
                state = State(5, z[0], z[1])
                pending = list(z[2:])
                predicted = predict_state(state, pending, 1, 0.5, dt) if controller == "predictor" else state
                command = pure_pursuit(predicted, (predicted.x+1, 0), 0.5, 0.6)
                moved = advance(state, pending[0], 1, 0.5, dt, "exact")
                return np.array([moved.y, moved.yaw]+pending[1:]+[command])
            jacobian = np.column_stack([(nonlinear(eps*np.eye(n+2)[j])-nonlinear(-eps*np.eye(n+2)[j]))/(2*eps)
                                        for j in range(n+2)])
            np.testing.assert_allclose(matrix, jacobian, atol=1e-8, rtol=1e-7)

    def test_continuous_boundary_scaling(self):
        a = continuous_delay_margin(1, 1)
        self.assertAlmostEqual(continuous_delay_margin(2, 1), a/2)
        self.assertAlmostEqual(continuous_delay_margin(1, 2), a*2)
        self.assertTrue(0.50 < a < 0.53)

    def test_delay_changes_linear_stability(self):
        self.assertLess(spectral_radius(augmented_matrix(1, 0.5, 1, 0.02, 10)), 1)
        self.assertGreater(spectral_radius(augmented_matrix(1, 0.5, 1, 0.02, 40)), 1)


if __name__ == "__main__":
    unittest.main()
