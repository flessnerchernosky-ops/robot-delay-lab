"""Local straight-path stability analysis; requires NumPy.

This is an unsaturated linear model, not a global nonlinear safety certificate.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from simulate import ROOT, write_csv


def continuous_delay_margin(speed, lookahead):
    frequency = math.sqrt(2.0+2.0*math.sqrt(2.0))
    return lookahead/speed*math.atan(frequency)/frequency


def augmented_matrix(speed, wheelbase, lookahead, dt, delay_steps, controller="pp"):
    if controller not in ("pp", "predictor"):
        raise ValueError("Unknown controller")
    if min(speed, wheelbase, lookahead, dt) <= 0 or delay_steps < 0:
        raise ValueError("Positive model parameters and a nonnegative delay required")
    n = int(delay_steps)
    if n != delay_steps:
        raise ValueError("delay_steps must be an integer")
    A = np.array([[1.0, speed*dt], [0.0, 1.0]])
    B = np.array([[speed*speed*dt*dt/(2.0*wheelbase)], [speed*dt/wheelbase]])
    K = np.array([[-2.0*wheelbase/lookahead**2, -2.0*wheelbase/lookahead]])
    if n == 0:
        return A+B@K
    matrix = np.zeros((n+2, n+2))
    matrix[:2, :2] = A
    matrix[:2, 2:3] = B
    for j in range(n-1):
        matrix[2+j, 3+j] = 1.0
    if controller == "pp":
        matrix[-1, :2] = K[0]
    else:
        matrix[-1, :2] = (K@np.linalg.matrix_power(A, n))[0]
        for j in range(n):
            matrix[-1, 2+j] = (K@np.linalg.matrix_power(A, n-1-j)@B).item()
    return matrix


def spectral_radius(matrix):
    return float(np.max(np.abs(np.linalg.eigvals(matrix))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT/"study_config.json")
    parser.add_argument("--out", type=Path, default=ROOT/"results_v02")
    args = parser.parse_args()
    plan = json.loads(args.config.read_text())
    base = plan["base"]
    rows, margins = [], []
    for speed in plan["speeds"]:
        for lookahead in (base["lookahead"],):
            first_unstable = None
            for n in range(round(plan["linear_max_delay"]/base["dt"])+1):
                for controller in ("pp", "predictor"):
                    radius = spectral_radius(augmented_matrix(speed, base["wheelbase"], lookahead,
                                                               base["dt"], n, controller))
                    rows.append(dict(speed_m_s=speed, lookahead_m=lookahead, delay_s=n*base["dt"],
                                     controller=controller, spectral_radius=radius,
                                     strictly_stable=radius < 1.0-1e-10))
                    if controller == "pp" and radius >= 1.0-1e-10 and first_unstable is None:
                        first_unstable = n*base["dt"]
            margins.append(dict(speed_m_s=speed, lookahead_m=lookahead, dt_s=base["dt"],
                                continuous_local_boundary_s=continuous_delay_margin(speed, lookahead),
                                first_sampled_nonstable_delay_s=first_unstable if first_unstable is not None else "",
                                last_sampled_stable_delay_s=(first_unstable-base["dt"]) if first_unstable is not None and first_unstable > 0 else ""))
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out/"linear_stability.csv", rows)
    write_csv(args.out/"linear_margins.csv", margins)
    for margin in margins:
        print(margin)


if __name__ == "__main__":
    main()
