"""Independent sampled linear-system and geometry checks. Python standard library only."""
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def verify():
    data = json.loads(subprocess.check_output(["node", "checks/arm_fixture.cjs"], cwd=ROOT))
    dt, beta, kp, kd = data["dt"], 0.3, data["settings"]["kp"], data["settings"]["kd"]
    # Exact ZOH state-space discretization of A=[[0,1],[0,-beta]], B=[[0],[1]].
    e = math.exp(-beta * dt)
    ad = ((1.0, (1 - e) / beta), (0.0, e))
    bd = ((dt - (1 - e) / beta) / beta, (1 - e) / beta)
    states = {kind: [[q, 0.0] for q in data["initial_q"]] for kind in ("p", "pd")}
    max_state_error = max_geometry_error = max_reference_error = 0.0
    for row in data["rows"]:
        gain_d = kd if row["kind"] == "pd" else 0.0
        for i, x in enumerate(states[row["kind"]]):
            # Closed-loop recurrence x[k+1] = (Ad - Bd*K)x[k] + Bd*Kp*q_ref.
            reference = data["reference_q"][i]
            next_x = [
                (ad[j][0] - bd[j] * kp) * x[0]
                + (ad[j][1] - bd[j] * gain_d) * x[1]
                + bd[j] * kp * reference
                for j in range(2)
            ]
            states[row["kind"]][i] = next_x
            max_state_error = max(max_state_error, abs(next_x[0] - row[f"q{i + 1}"]),
                                  abs(next_x[1] - row[f"v{i + 1}"]))
            max_reference_error = max(max_reference_error, abs(reference - row[f"ref_q{i + 1}"]))
            if abs(row[f"command{i + 1}"]) >= 6 or abs(row[f"v{i + 1}"]) >= 100:
                raise AssertionError("Fixture reached a limit; linear reference is invalid")
        q1, q2 = row["q1"], row["q2"]
        position = (math.cos(q1) + .8 * math.cos(q1 + q2),
                    math.sin(q1) + .8 * math.sin(q1 + q2))
        max_geometry_error = max(max_geometry_error, abs(position[0] - row["x"]),
                                 abs(position[1] - row["y"]))
        expected_error = math.hypot(position[0] - row["target_x"], position[1] - row["target_y"])
        max_geometry_error = max(max_geometry_error, abs(expected_error - row["error"]))
    assert max_state_error < 1e-8, max_state_error
    assert max_geometry_error < 1e-10, max_geometry_error
    assert max_reference_error < 1e-10, max_reference_error
    result = {"fixture_rows": len(data["rows"]), "max_state_error": max_state_error,
              "max_geometry_error_m": max_geometry_error, "max_reference_error_rad": max_reference_error,
              "scope": "Fixed target, no delay, unsaturated independent servos. Does not validate real robot dynamics."}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    verify()
