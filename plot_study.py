"""Generate v0.2 comparison, sensitivity, theory figures and optional GIF."""
import argparse
import csv
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import TwoSlopeNorm
import numpy as np
from simulate import ROOT, make_route

COLORS = {"pp": "#d34d66", "predictor": "#157f91"}
LABELS = {"pp": "Pure Pursuit", "predictor": "Predicted-state PP"}


def read_csv(path):
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def save(fig, directory, name):
    fig.savefig(directory/f"{name}.png", dpi=160, bbox_inches="tight")
    fig.savefig(directory/f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT/"results_v02")
    parser.add_argument("--gif", action="store_true")
    args = parser.parse_args()
    directory = args.results
    rows = read_csv(directory/"summary.csv")
    pairs = read_csv(directory/"paired_comparison.csv")
    plan = json.loads((directory/"plan_used.json").read_text())
    base = plan["base"]
    window_label = f"First-{base['evaluation_distance_m']:g}-m RMSE (m)"
    main_rows = [r for r in rows if r["group"] in ("comparison", "holdout")]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    fig, axes = plt.subplots(1, len(plan["speeds"]), figsize=(14, 4.4), squeeze=False)
    for ax, speed in zip(axes[0], plan["speeds"]):
        for controller in ("pp", "predictor"):
            values = [[float(r["rmse_m"]) for r in main_rows if r["controller"] == controller
                       and float(r["speed_m_s"]) == speed and float(r["delay_s"]) == delay
                       and r["evaluation_reached"] == "True"] for delay in plan["delays"]]
            if not all(values):
                raise ValueError("Missing completed evaluation window in comparison plot")
            ax.plot(plan["delays"], [statistics.mean(v) for v in values], "o-",
                    color=COLORS[controller], label=LABELS[controller])
            ax.fill_between(plan["delays"], [min(v) for v in values], [max(v) for v in values], color=COLORS[controller], alpha=0.12)
        ax.set(title=f"Speed {speed:g} m/s", xlabel="Actual steering delay (s)", ylabel=window_label)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8, loc="upper left")
    route_count = len(plan["development_routes"])+len(plan["holdout_routes"])
    fig.suptitle(f"Lookahead {base['lookahead']:g} m | mean and range over {route_count} routes | each panel has its own y-scale", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, directory, "controller_comparison")

    routes = plan["development_routes"]+plan["holdout_routes"]
    labels, values = [], []
    for speed in plan["speeds"]:
        for route in routes:
            labels.append(f"{route} | {speed:g} m/s")
            values.append([float(next(p["rmse_improvement_percent"] for p in pairs
                                    if p["route"] == route and float(p["speed_m_s"]) == speed
                                    and float(p["delay_s"]) == delay and p["both_windows_reached"] == "True"))
                           for delay in plan["delays"]])
    fig, ax = plt.subplots(figsize=(9, 8))
    array = np.array(values)
    im = ax.imshow(array, cmap="RdYlGn", norm=TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100), aspect="auto")
    ax.set_xticks(range(len(plan["delays"])), [f"{d:g} s" for d in plan["delays"]])
    ax.set_yticks(range(len(labels)), labels)
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            ax.text(j, i, f"{array[i, j]:+.1f}%", ha="center", va="center", fontsize=9)
    ax.set(xlabel="Actual steering delay", title="Paired RMSE reduction | positive = predictor better, negative = worse")
    fig.colorbar(im, ax=ax, label="100 x (PP RMSE - predictor RMSE) / PP RMSE (%)", shrink=0.8)
    fig.tight_layout()
    save(fig, directory, "paired_improvement")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    route_colors = ["#157f91", "#9154a0"]
    for i, route in enumerate(plan["sensitivity_routes"]):
        selected = [r for r in rows if r["group"] == "delay_mismatch" and r["route"] == route]
        axes[0].plot([float(r["estimated_delay_s"])-float(r["delay_s"]) for r in selected],
                     [float(r["rmse_m"]) for r in selected], "o-", label=route, color=route_colors[i])
        selected = [r for r in rows if r["group"] == "model_mismatch" and r["route"] == route]
        axes[1].plot([float(r["model_scale"]) for r in selected], [float(r["rmse_m"]) for r in selected], "o-", label=route, color=route_colors[i])
    axes[0].axvline(0, color="#777777", ls="--", lw=1)
    axes[1].axvline(1, color="#777777", ls="--", lw=1)
    axes[0].set(title="Error in assumed delay", xlabel="Assumed delay - actual delay (s)", ylabel=window_label)
    axes[1].set(title="Error in assumed wheelbase", xlabel="Model wheelbase / actual wheelbase", ylabel=window_label)
    for ax in axes:
        ax.grid(alpha=0.2)
        ax.legend()
    fig.suptitle(f"Predictor sensitivity | delay {plan['sensitivity_delay']:g} s, speed {plan['study_speed']:g} m/s, lookahead {base['lookahead']:g} m")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, directory, "model_sensitivity")

    fig, axes = plt.subplots(1, len(plan["development_routes"]), figsize=(14, 4.3), squeeze=False)
    for ax, route in zip(axes[0], plan["development_routes"]):
        for controller in ("pp", "predictor"):
            selected = [r for r in rows if r["group"] == "lookahead" and r["route"] == route and r["controller"] == controller]
            ax.plot([float(r["lookahead_m"]) for r in selected], [float(r["rmse_m"]) for r in selected], "o-", label=LABELS[controller], color=COLORS[controller])
        ax.set(title=route, xlabel="Lookahead (m)", ylabel=window_label)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8)
    fig.suptitle(f"Predeclared sweep | speed {plan['study_speed']:g} m/s, delay {plan['sensitivity_delay']:g} s; no tuned winner selected")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, directory, "lookahead_tradeoff")

    linear = read_csv(directory/"linear_stability.csv")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for i, speed in enumerate(plan["speeds"]):
        for controller, style in (("pp", "-"), ("predictor", "--")):
            selected = [r for r in linear if float(r["speed_m_s"]) == speed and r["controller"] == controller]
            ax.plot([float(r["delay_s"]) for r in selected], [float(r["spectral_radius"]) for r in selected], style,
                    color=["#5268ad", "#d27b2e", "#42835b"][i], label=f"{LABELS[controller]}, {speed:g} m/s")
    ax.axhline(1, color="#30394b", ls=":", label="Local stability boundary")
    ax.set(xlabel="Delay (s)", ylabel="Spectral radius of augmented matrix",
           title="Straight path, infinitesimal errors, no steering saturation | sampled linear model")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8, ncol=2, loc="lower right")
    fig.tight_layout()
    save(fig, directory, "local_stability")

    if args.gif:
        selected = [r for r in main_rows if r["route"] == "s_curve" and float(r["speed_m_s"]) == plan["study_speed"] and float(r["delay_s"]) == plan["sensitivity_delay"]]
        if {r["controller"] for r in selected} != {"pp", "predictor"}:
            raise ValueError("GIF needs an S-curve comparison pair at study_speed and sensitivity_delay")
        logs = {r["controller"]: [{k: float(v) for k, v in row.items()} for row in read_csv(directory/"logs"/f"{r['case_id']}.csv")]
                for r in selected}
        fig, ax = plt.subplots(figsize=(9, 3.8))
        ax.plot(*zip(*make_route("s_curve", plan["base"]["route_samples"])), "--", color="#273447", label="Reference")
        lines, dots = {}, {}
        for controller in ("pp", "predictor"):
            lines[controller], = ax.plot([], [], color=COLORS[controller], lw=1.8, label=LABELS[controller])
            dots[controller], = ax.plot([], [], "o", color=COLORS[controller], ms=6)
        ax.set(xlim=(-1, 22), ylim=(-4, 4), xlabel="x (m)", ylabel="y (m)", aspect="equal")
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8, loc="upper right")
        title = ax.set_title("")
        max_time = max(v[-1]["time_s"] for v in logs.values())
        def frame(index):
            time = max_time*index/119
            for controller in ("pp", "predictor"):
                values = logs[controller][:max(1, int(time/plan["base"]["dt"])+1)]
                lines[controller].set_data([v["x_m"] for v in values], [v["y_m"] for v in values])
                dots[controller].set_data([values[-1]["x_m"]], [values[-1]["y_m"]])
            title.set_text(f"Same plant delay {plan['sensitivity_delay']:g} s | t = {time:.1f} s (accelerated playback)")
            return list(lines.values())+list(dots.values())+[title]
        fig.tight_layout()
        animation = FuncAnimation(fig, frame, frames=120, interval=80)
        animation.save(directory/"comparison_demo.gif", writer=PillowWriter(fps=12), dpi=100)
        plt.close(fig)
    print(f"Saved v0.2 figures to {directory}")


if __name__ == "__main__":
    main()
