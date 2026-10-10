"""Plot saved experiment logs. Install requirements.txt before running."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from simulate import ROOT, case_stem, make_route


def read_rows(path):
    with path.open(encoding="utf-8") as stream:
        return [{key: float(value) for key, value in row.items()} for row in csv.DictReader(stream)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT/"results")
    parser.add_argument("--gif", action="store_true", help="Also render an S-curve animation")
    args = parser.parse_args()
    config = json.loads((args.results/"config_used.json").read_text())
    colors = ["#147d92", "#5c9a34", "#dd9429", "#ca4965"]
    with (args.results/"summary.csv").open() as stream:
        summary = list(csv.DictReader(stream))
    logs = {(name, delay): read_rows(args.results/f"{case_stem(name, delay)}.csv")
            for name in config["routes"] for delay in config["delays"]}
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(len(config["routes"]), 2, figsize=(12, 3.5*len(config["routes"])), squeeze=False)
    for r, name in enumerate(config["routes"]):
        reference = make_route(name)
        axes[r, 0].plot(*zip(*reference), "--", color="#263449", lw=2, label="Reference")
        for i, delay in enumerate(config["delays"]):
            rows = logs[name, delay]
            score = next(s for s in summary if s["route"] == name and float(s["delay_s"]) == delay)
            label = f"Delay {delay:g} s" + (" (goal missed)" if score["completed"] == "False" else "")
            color = colors[i % len(colors)]
            axes[r, 0].plot([v["x_m"] for v in rows], [v["y_m"] for v in rows], color=color, label=label, lw=1.3)
            window = [v for v in rows if v["time_s"] <= float(score["evaluation_duration_s"])]
            axes[r, 1].plot([v["time_s"] for v in window], [v["error_m"] for v in window], color=color, label=label)
        axes[r, 0].set(title=f"{name}: full trajectory", xlabel="x (m)", ylabel="y (m)", aspect="equal")
        if name in ("straight", "s_curve"):
            axes[r, 0].set(xlim=(-1, 22), ylim=(-4, 4))
        axes[r, 1].set(title=f"{name}: first {config['evaluation_distance_m']:g} m of path progress", xlabel="Time (s)", ylabel="Distance to reference (m)")
        for ax in axes[r]:
            ax.grid(alpha=0.2)
            ax.legend(fontsize=8, framealpha=1)
    fig.suptitle("Pure Pursuit under steering-command delay | deterministic simulation", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(args.results/"overview.png", dpi=160)
    fig.savefig(args.results/"overview.svg")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for r, name in enumerate(config["routes"]):
        scores = [s for s in summary if s["route"] == name]
        reached = [s for s in scores if s["evaluation_reached"] == "True"]
        ax.plot([float(s["delay_s"]) for s in reached], [float(s["rmse_m"]) for s in reached], "o-", label=name)
    ax.set(xlabel="Steering-command delay (s)", ylabel="Cross-track RMSE (m)",
           title=f"Tracking error over first {config['evaluation_distance_m']:g} m of path progress")
    ax.text(0.02, 0.98, "Fixed settings; one deterministic run per case\nUnreached evaluation windows are excluded", transform=ax.transAxes, va="top", fontsize=9)
    ax.grid(alpha=0.2)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(args.results/"delay_vs_error.png", dpi=160)
    fig.savefig(args.results/"delay_vs_error.svg")
    plt.close(fig)

    if args.gif and "s_curve" in config["routes"]:
        fig, ax = plt.subplots(figsize=(9, 3.7))
        ax.plot(*zip(*make_route("s_curve")), "--", color="#263449", label="Reference")
        lines, dots = [], []
        for i, delay in enumerate(config["delays"]):
            color = colors[i % len(colors)]
            line, = ax.plot([], [], color=color, lw=1.5, label=f"Delay {delay:g} s")
            dot, = ax.plot([], [], "o", color=color, ms=5)
            lines.append(line)
            dots.append(dot)
        ax.set(xlim=(-1, 22), ylim=(-4, 4), xlabel="x (m)", ylabel="y (m)", aspect="equal")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(alpha=0.2)
        clock_label = ax.set_title("")
        duration = max(logs["s_curve", d][-1]["time_s"] for d in config["delays"])

        def frame(index):
            time = duration*index/119
            for i, delay in enumerate(config["delays"]):
                rows = logs["s_curve", delay]
                count = min(len(rows), int(time/config["dt"])+1)
                shown = rows[:count]
                lines[i].set_data([v["x_m"] for v in shown], [v["y_m"] for v in shown])
                dots[i].set_data([shown[-1]["x_m"]], [shown[-1]["y_m"]])
            clock_label.set_text(f"S-curve tracking | simulated time {time:.1f} s (playback accelerated)")
            return lines+dots+[clock_label]

        fig.tight_layout()
        animation = FuncAnimation(fig, frame, frames=120, interval=80, blit=False)
        animation.save(args.results/"tracking_demo.gif", writer=PillowWriter(fps=12), dpi=100)
        plt.close(fig)
    print(f"Charts saved to {args.results}")


if __name__ == "__main__":
    main()
