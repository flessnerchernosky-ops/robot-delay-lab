"""Pure Pursuit and command-delay experiments; Python standard library only.

Positions refer to the rear axle of a kinematic bicycle, in metres/radians.
Run: python simulate.py
"""
import argparse
import csv
import json
import math
from collections import deque
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent


@dataclass
class State:
    x: float
    y: float
    yaw: float


class DelayLine:
    """A command generated at step k is applied at step k + steps.

    Before commands arrive, steering is zero. Delay applies to steering only.
    """
    def __init__(self, steps):
        if steps < 0 or int(steps) != steps:
            raise ValueError("Delay steps must be a non-negative integer")
        self.queue = deque([0.0] * int(steps))

    def push(self, command):
        self.queue.append(command)
        return self.queue.popleft()


def make_route(name, samples=201):
    points = []
    for i in range(samples):
        u = i / (samples - 1)
        if name == "straight":
            point = (20.0 * u, 0.0)
        elif name == "s_curve":
            point = (20.0 * u, 2.0 * math.sin(2.0 * math.pi * u))
        elif name == "arc":
            angle = math.pi * u / 2.0
            point = (12.0 * math.sin(angle), 12.0 * (1.0 - math.cos(angle)))
        elif name == "tight_s":
            point = (20.0*u, 1.5*math.sin(4.0*math.pi*u))
        elif name == "lane_change":
            point = (20.0*u, 1.5*(math.tanh((20.0*u-10.0)/2.0)+math.tanh(5.0)))
        else:
            raise ValueError(f"Unknown route: {name}")
        points.append(point)
    return points


class Route:
    def __init__(self, points):
        self.points = points
        self.distances = [0.0]
        for a, b in zip(points, points[1:]):
            self.distances.append(self.distances[-1] + math.hypot(b[0]-a[0], b[1]-a[1]))

    def project(self, x, y):
        """Return nearest distance and arc-length progress on the polyline."""
        best = (float("inf"), 0.0)
        for i, (a, b) in enumerate(zip(self.points, self.points[1:])):
            dx, dy = b[0]-a[0], b[1]-a[1]
            length2 = dx*dx + dy*dy
            fraction = max(0.0, min(1.0, ((x-a[0])*dx + (y-a[1])*dy) / length2))
            distance = math.hypot(x-a[0]-fraction*dx, y-a[1]-fraction*dy)
            if distance < best[0]:
                best = (distance, self.distances[i] + fraction*math.sqrt(length2))
        return best

    def at(self, progress):
        progress = max(0.0, min(progress, self.distances[-1]))
        for i in range(len(self.points)-1):
            if progress <= self.distances[i+1]:
                fraction = (progress-self.distances[i]) / (self.distances[i+1]-self.distances[i])
                a, b = self.points[i], self.points[i+1]
                return (a[0]+fraction*(b[0]-a[0]), a[1]+fraction*(b[1]-a[1]))
        return self.points[-1]


def pure_pursuit(state, target, wheelbase, max_steer):
    # Rotate the target into the vehicle frame. Positive local y means left.
    dx, dy = target[0]-state.x, target[1]-state.y
    local_y = -math.sin(state.yaw)*dx + math.cos(state.yaw)*dy
    curvature = 2.0 * local_y / max(dx*dx + dy*dy, 1e-12)
    steering = math.atan(wheelbase * curvature)
    return max(-max_steer, min(max_steer, steering))


def advance(state, steering, speed, wheelbase, dt, method="euler"):
    """Integrate one interval; exact mode assumes constant speed/steering."""
    if method == "exact":
        angle = speed/wheelbase*math.tan(steering)*dt
        half = angle/2.0
        sinc = math.sin(half)/half if abs(half) > 1e-8 else 1.0-half*half/6.0
        distance = speed*dt*sinc
        return State(state.x+distance*math.cos(state.yaw+half),
                     state.y+distance*math.sin(state.yaw+half), state.yaw+angle)
    if method != "euler":
        raise ValueError(f"Unknown integrator: {method}")
    return State(
        state.x + speed*math.cos(state.yaw)*dt,
        state.y + speed*math.sin(state.yaw)*dt,
        state.yaw + speed/wheelbase*math.tan(steering)*dt,
    )


def predict_state(state, pending_commands, speed, model_wheelbase, dt, method="exact"):
    """Roll out only known past commands; never reads future plant states."""
    predicted = State(state.x, state.y, state.yaw)
    for steering in pending_commands:
        predicted = advance(predicted, steering, speed, model_wheelbase, dt, method)
    return predicted


def validate(config):
    for key in ("dt", "speed", "wheelbase", "lookahead", "max_time", "goal_tolerance", "evaluation_distance_m"):
        if not math.isfinite(config[key]) or config[key] <= 0:
            raise ValueError(f"{key} must be finite and positive")
    if not 0 < config["max_steer_deg"] < 90:
        raise ValueError("max_steer_deg must be between 0 and 90")
    if not math.isfinite(config["initial_lateral_offset"]):
        raise ValueError("initial_lateral_offset must be finite")
    if not config["routes"] or not config["delays"]:
        raise ValueError("Specify at least one route and delay")
    samples = config.get("route_samples", 201)
    if not isinstance(samples, int) or samples < 2:
        raise ValueError("route_samples must be an integer >= 2")
    if config.get("integrator", "euler") not in ("euler", "exact"):
        raise ValueError("integrator must be euler or exact")
    for delay in config["delays"]:
        steps = delay/config["dt"]
        if delay < 0 or not math.isfinite(delay) or not math.isclose(steps, round(steps), abs_tol=1e-9):
            raise ValueError("Each delay must be a non-negative integer multiple of dt")
    for name in config["routes"]:
        if config["evaluation_distance_m"] > Route(make_route(name, samples)).distances[-1]:
            raise ValueError("Evaluation distance must not exceed any route length")


def run_case(config, name, delay, controller="pp", estimated_delay=None, model_scale=1.0):
    if controller not in ("pp", "predictor"):
        raise ValueError("controller must be pp or predictor")
    estimated_delay = delay if estimated_delay is None else estimated_delay
    if not math.isfinite(model_scale) or model_scale <= 0:
        raise ValueError("model_scale must be finite and positive")
    for value in (delay, estimated_delay):
        steps = value/config["dt"]
        if not math.isfinite(value) or value < 0 or not math.isclose(steps, round(steps), abs_tol=1e-9):
            raise ValueError("Plant and estimated delays must be non-negative multiples of dt")
    method = config.get("integrator", "euler")
    route = Route(make_route(name, config.get("route_samples", 201)))
    a, b = route.points[:2]
    heading = math.atan2(b[1]-a[1], b[0]-a[0])
    offset = config["initial_lateral_offset"]
    state = State(a[0]-offset*math.sin(heading), a[1]+offset*math.cos(heading), heading)
    line = DelayLine(round(delay/config["dt"]))
    # Separate controller-side command history, driven by its OWN delay estimate.
    # The predictor cannot inspect the actual plant's queue.
    assumed_line = DelayLine(round(estimated_delay/config["dt"]))
    model_wheelbase = config["wheelbase"]*model_scale
    limit = math.radians(config["max_steer_deg"])
    rows = []
    completed = False
    for step in range(int(config["max_time"]/config["dt"])+1):
        error, progress = route.project(state.x, state.y)
        goal_distance = math.hypot(state.x-route.points[-1][0], state.y-route.points[-1][1])
        completed = (goal_distance <= config["goal_tolerance"] and
                     progress >= route.distances[-1]-config["goal_tolerance"])
        control_state = state
        control_progress = progress
        if controller == "predictor":
            control_state = predict_state(state, tuple(assumed_line.queue), config["speed"],
                                          model_wheelbase, config["dt"], method)
            _, control_progress = route.project(control_state.x, control_state.y)
        target = route.at(control_progress+config["lookahead"])
        command = pure_pursuit(control_state, target,
                               model_wheelbase if controller == "predictor" else config["wheelbase"], limit)
        assumed_line.push(command)
        applied = line.push(command)
        rows.append(dict(time_s=step*config["dt"], x_m=state.x, y_m=state.y,
                         yaw_rad=state.yaw, error_m=error, progress_m=progress,
                         command_rad=command, applied_rad=applied))
        if controller == "predictor":
            rows[-1].update(predicted_x_m=control_state.x, predicted_y_m=control_state.y,
                            predicted_yaw_rad=control_state.yaw)
        if completed:
            break
        state = advance(state, applied, config["speed"], config["wheelbase"], config["dt"], method)
    # Compare the same first section of each route, avoiding endpoint manoeuvres.
    # An unreached window remains explicitly flagged; it is not a completed score.
    cutoff = next((i for i, row in enumerate(rows)
                   if row["progress_m"] >= config["evaluation_distance_m"]), None)
    evaluation = rows if cutoff is None else rows[:cutoff+1]
    errors = [row["error_m"] for row in evaluation]
    summary = dict(route=name, delay_s=delay, completed=completed,
                   evaluation_reached=cutoff is not None,
                   evaluation_distance_m=config["evaluation_distance_m"],
                   evaluation_duration_s=evaluation[-1]["time_s"],
                   duration_s=rows[-1]["time_s"],
                   rmse_m=math.sqrt(sum(e*e for e in errors)/len(errors)),
                   max_error_m=max(errors), final_error_m=rows[-1]["error_m"],
                   full_run_rmse_m=math.sqrt(sum(row["error_m"]**2 for row in rows)/len(rows)),
                   final_progress_fraction=min(1.0, rows[-1]["progress_m"]/route.distances[-1]))
    return rows, summary


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def case_stem(name, delay):
    return f"{name}_delay_{delay:.3f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT/"config.json")
    parser.add_argument("--out", type=Path, default=ROOT/"results")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate(config)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/"config_used.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    summaries = []
    for name in config["routes"]:
        for delay in config["delays"]:
            rows, summary = run_case(config, name, delay)
            write_csv(args.out/f"{case_stem(name, delay)}.csv", rows)
            summaries.append(summary)
            print(f"{name:10} delay={delay:.2f}s window_RMSE={summary['rmse_m']:.4f}m completed={summary['completed']}")
    write_csv(args.out/"summary.csv", summaries)


if __name__ == "__main__":
    main()
