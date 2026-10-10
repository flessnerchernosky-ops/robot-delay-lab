# Robot Delay Lab

[中文](README.md) · [English](README.en.md)

Hardware-free robotics experiments, from reproducible Python studies to beginner-friendly browser playgrounds. MIT licensed and AI-assisted. These are educational models, without hardware validation or a claim of algorithmic novelty.

## Episode 3: Catch the Stars

**[Play in English](https://flessnerchernosky-ops.github.io/robot-delay-lab/arm/?lang=en)** · [中文试玩](https://flessnerchernosky-ops.github.io/robot-delay-lab/arm/)

Two robot arms pursue the same star: position-only feedback (P), and position plus velocity feedback (PD). Five challenges explore reachability, overshooting, delayed commands, joint limits and moving targets. No hardware or installation; the interface switches between Chinese and English.

Drag targets, tune parameters, download full CSV trajectories, save your own experiment notes, and check single-variable comparisons. Included: 31 configuration entries (with repeated baselines), 62 deterministic trajectories, 15 model checks, and an independent Python sampled-linear-system verification.

[English model and reproduction guide](EPISODE_03.en.md) · [中文说明](EPISODE_03.zh-CN.md) · [Benchmark scores](examples/arm/summary.csv) · [Model source](docs/arm/engine.js)

This is a two-link, independent-servo teaching model. It omits gravity, joint coupling, collisions, grippers and contact. Results cannot be directly applied to real robot arms.

![Catch the Stars browser playground](docs/arm/preview.jpg)

From the repository root, using Node.js and Python 3.10+:

```text
node checks/arm.cjs
python verify_arm.py
node checks/arm_examples.cjs
```

Open `docs/arm/index.html` for offline play. No external fonts, scripts, backend or experiment uploads. Notes stay in the current page and are cleared on refresh; download them before leaving.

## Episode 2: Star Chase Lab

**[Play Star Chase](https://flessnerchernosky-ops.github.io/robot-delay-lab/)** — a fictional sliding spacecraft makes feedback, command delay and prediction visible. Five presets, manual driving, error curves, CSV export and a completed-run notebook. The earlier interface and its learning materials are currently in Chinese.

[Episode 2 guide, Chinese](EPISODE_02.md) · [15-minute learning path, Chinese](LEARNING_MISSIONS.md) · [Browser source](docs/)

Open `docs/index.html` offline. The one-dimensional spacecraft has limited propulsion, drag and queued commands. Prediction uses current velocity and pending inputs, assumes short-term target velocity, and can fail when the target changes suddenly. The zero-delay controller is a reference; it does not share the delayed controllers’ input timing.

```text
node checks/star_lab.cjs
node checks/notebook.cjs
```

## Episode 1: Robot path-tracking study

Research question: when does Pure Pursuit oscillate with steering-command delay, and when does command-history prediction help or hurt?

Version 0.2 compares ordinary and predicted-state Pure Pursuit with a two-dimensional kinematic bicycle model. It includes 182 deterministic trajectories, 16 Python checks, five routes, three speeds, model/delay estimation errors, discretization diagnostics and local stability analysis. The original v0.1 results remain in `results/`. No MPC, stochastic noise or hardware experiments are included.

The principal finding is that prediction does not improve every condition. [v0.2 report](REPORT_V02.md) and [local stability analysis](THEORY.md) contain the results and assumptions; these detailed earlier documents are in Chinese.

![Controller comparison](results_v02/comparison_demo.gif)

### Reproduce v0.2

Core simulation uses Python standard library. Plotting, matrix spectra and the complete test suite need the dependencies listed in `requirements.txt`. Python 3.12 matches the validation environment.

```text
python study.py
python -m pip install -r requirements.txt
python linear_analysis.py
python -m unittest -v
python plot_study.py --gif
python build_report.py
```

Without NumPy, four linear-model tests explicitly skip. `study_config.json` contains study settings; `results_v02/manifest.json` records each trajectory’s settings and `paired_comparison.csv` includes both improvements and regressions. Cross-route ranges are not statistical confidence intervals. Included study results are dated 2026-10-09. Use `--out` to preserve them, and matching `--results` options for plots and reports; `build_report.py --date` sets the actual experiment date.

### Original baseline

```text
python simulate.py
python -m unittest -v
python -m pip install -r requirements.txt
python plot_results.py --gif
```

To write a separate experiment:

```text
python simulate.py --config config.json --out results_experiment_01
python plot_results.py --results results_experiment_01 --gif
```

Default conditions: 0.02 s step, 1 m/s constant speed, 0.5 m wheelbase, 1 m route lookahead, ±35° steering, 0.5 m initial cross-track offset, and delays of 0/0.2/0.5/0.8 s. Maximum duration is 60 s; primary tracking metrics cover the first 15 m of route progress. Settings are saved with each experiment.

The model uses `x'=v*cos(yaw)`, `y'=v*sin(yaw)`, `yaw'=v/L*tan(delta)`. The original baseline uses forward Euler; v0.2 uses exact constant-input arc updates. Pure Pursuit projects onto the route and selects a target by along-route lookahead, then computes steering from its vehicle-frame lateral offset and Euclidean distance. See [Coulter’s original report](https://publications.ri.cmu.edu/implementation-of-the-pure-pursuit-path-tracking-algorithm).

Only steering commands are delayed. Controllers read current true state. There is no perception delay, noise, actuator dynamics, tire slip or collision model, and speed is not delayed. Delays must be integer multiples of the simulation step.

`rmse_m` and `max_error_m` include the initial transient over the evaluation interval. Check `evaluation_reached`, `completed` and `evaluation_duration_s` as well: a failed run may cover less distance. RMSE is time sampled, not distance averaged. Included v0.1 results reach the evaluation distance in all 12 cases, with 11 completions; one high-delay straight-route case fails the terminal condition. These deterministic results have no statistical confidence intervals.

### Main study files

| File | Purpose |
|---|---|
| `simulate.py`, `config.json` | Baseline model, delay queue, routes and settings |
| `study.py`, `study_config.json` | v0.2 experiment generation |
| `linear_analysis.py`, `THEORY.md` | Local sampled-system spectra and derivation |
| `plot_study.py`, `build_report.py` | Study figures, animations and report |
| `plot_results.py` | Baseline figures and animation |
| `test_simulate.py`, `test_study.py` | Model, prediction and linear-analysis checks |
| `LEARNING.md`, `REPORT.md`, `REPORT_V02.md` | Earlier learning and research materials, Chinese |

## References and contributions

[PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) and [Robotics Toolbox for Python](https://github.com/petercorke/robotics-toolbox-python) inform the arm module’s teaching approach. Its simplified implementation is original, with no copied upstream code or runtime dependencies on these repositories.

For issues, include full settings, interface language, exported CSV and expected/actual behavior. Contributions should preserve fair comparisons, reproducible parameters and explicit limitations. Stars can help people discover the project; they are not evidence of research novelty or validation.
