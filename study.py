"""Reproducible controller comparison; no third-party packages required.

Run python study.py. v0.1 results/ is preserved; outputs go to results_v02/.
"""
import argparse
import csv
import json
import math
from pathlib import Path

from simulate import ROOT, make_route, Route, run_case, validate, write_csv


def window_metrics(rows, summary, dt):
    window = [row for row in rows if row["time_s"] <= summary["evaluation_duration_s"]]
    # Error after an initial section; this is a diagnostic, not a replacement score.
    later = [row["error_m"] for row in window if row["progress_m"] >= 2.0]
    rates = [(b["applied_rad"]-a["applied_rad"])/dt for a, b in zip(window, window[1:])]
    return dict(post_2m_rmse_m=math.sqrt(sum(e*e for e in later)/len(later)) if later else "",
                steering_rate_rms_rad_s=math.sqrt(sum(r*r for r in rates)/len(rates)) if rates else 0.0)


def prediction_residual(rows, delay_steps):
    """Offline diagnostic only: compare earlier prediction with later plant state."""
    if "predicted_x_m" not in rows[0] or len(rows) <= delay_steps:
        return ""
    errors = [math.hypot(a["predicted_x_m"]-b["x_m"], a["predicted_y_m"]-b["y_m"])
              for a, b in zip(rows, rows[delay_steps:])]
    return max(errors)


def make_cases(plan):
    cases = []
    base = plan["base"]

    def add(group, route, speed, delay, controller, *, lookahead=None, bias=0.0,
            scale=1.0, dt=None, samples=None, integrator=None):
        config = dict(base, speed=speed, routes=[route], delays=[delay])
        config.update(lookahead=base["lookahead"] if lookahead is None else lookahead,
                      dt=base["dt"] if dt is None else dt,
                      route_samples=base["route_samples"] if samples is None else samples,
                      integrator=base["integrator"] if integrator is None else integrator)
        estimate = delay+bias
        if estimate < 0:
            raise ValueError("A delay bias produced a negative assumed delay")
        validate(config)
        for value in (estimate,):
            if not math.isclose(value/config["dt"], round(value/config["dt"]), abs_tol=1e-9):
                raise ValueError("Estimated delays must be integer multiples of dt")
        cases.append(dict(group=group, route=route, controller=controller, config=config,
                          delay_s=delay, estimated_delay_s=estimate, model_scale=scale))

    for routes, group in ((plan["development_routes"], "comparison"),
                          (plan["holdout_routes"], "holdout")):
        for route in routes:
            for speed in plan["speeds"]:
                for delay in plan["delays"]:
                    for controller in ("pp", "predictor"):
                        add(group, route, speed, delay, controller)

    # Predeclared sweeps, using development routes only; no best-setting selection.
    for route in plan["development_routes"]:
        for lookahead in plan["lookaheads"]:
            for controller in ("pp", "predictor"):
                add("lookahead", route, plan["study_speed"], plan["sensitivity_delay"], controller,
                    lookahead=lookahead)
    for route in plan["sensitivity_routes"]:
        for bias in plan["delay_biases"]:
            add("delay_mismatch", route, plan["study_speed"], plan["sensitivity_delay"], "predictor", bias=bias)
        for scale in plan["model_scales"]:
            add("model_mismatch", route, plan["study_speed"], plan["sensitivity_delay"], "predictor", scale=scale)
    for dt in plan["sampling_periods"]:
        for samples in plan["route_samples_options"]:
            for integrator in ("euler", "exact"):
                for controller in ("pp", "predictor"):
                    add("numerics", "s_curve", plan["study_speed"], plan["sensitivity_delay"], controller,
                        dt=dt, samples=samples, integrator=integrator)
    return cases


def compare_pairs(scores):
    pairs = []
    baseline = {(s["group"], s["route"], s["speed_m_s"], s["delay_s"]): s
                for s in scores if s["group"] in ("comparison", "holdout") and s["controller"] == "pp"}
    for score in scores:
        if score["group"] not in ("comparison", "holdout") or score["controller"] != "predictor":
            continue
        original = baseline[score["group"], score["route"], score["speed_m_s"], score["delay_s"]]
        valid = score["evaluation_reached"] and original["evaluation_reached"]
        improvement = 100*(original["rmse_m"]-score["rmse_m"])/original["rmse_m"] if valid and original["rmse_m"] > 1e-12 else ""
        pairs.append(dict(group=score["group"], route=score["route"], speed_m_s=score["speed_m_s"],
                          delay_s=score["delay_s"], both_windows_reached=valid,
                          pp_rmse_m=original["rmse_m"], predictor_rmse_m=score["rmse_m"],
                          rmse_improvement_percent=improvement,
                          pp_completed=original["completed"], predictor_completed=score["completed"],
                          pp_case=original["case_id"], predictor_case=score["case_id"]))
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT/"study_config.json")
    parser.add_argument("--out", type=Path, default=ROOT/"results_v02")
    args = parser.parse_args()
    plan = json.loads(args.config.read_text(encoding="utf-8"))
    if set(plan["development_routes"]) & set(plan["holdout_routes"]):
        raise ValueError("Development and holdout routes must be disjoint")
    cases = make_cases(plan)
    args.out.mkdir(parents=True, exist_ok=True)
    logs = args.out/"logs"
    logs.mkdir(exist_ok=True)
    (args.out/"plan_used.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    manifest, scores = [], []
    for i, case in enumerate(cases, 1):
        case_id = f"case_{i:04}"
        config = case["config"]
        rows, summary = run_case(config, case["route"], case["delay_s"], case["controller"],
                                 case["estimated_delay_s"], case["model_scale"])
        score = dict(case_id=case_id, group=case["group"], controller=case["controller"],
                     speed_m_s=config["speed"], lookahead_m=config["lookahead"],
                     dt_s=config["dt"], route_samples=config["route_samples"], integrator=config["integrator"],
                     estimated_delay_s=case["estimated_delay_s"], model_scale=case["model_scale"], **summary)
        score.update(window_metrics(rows, summary, config["dt"]))
        score["max_prediction_position_residual_m"] = prediction_residual(rows, round(case["estimated_delay_s"]/config["dt"]))
        scores.append(score)
        write_csv(logs/f"{case_id}.csv", rows)
        manifest.append(dict(case_id=case_id, **case))
        if i % 20 == 0 or i == len(cases):
            print(f"Completed {i}/{len(cases)} cases", flush=True)
    write_csv(args.out/"summary.csv", scores)
    write_csv(args.out/"paired_comparison.csv", compare_pairs(scores))
    (args.out/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved {len(scores)} cases to {args.out}")


if __name__ == "__main__":
    main()
