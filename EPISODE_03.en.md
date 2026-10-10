# Episode 3: Catch the Stars

[中文](EPISODE_03.zh-CN.md) · [English](EPISODE_03.en.md)

**[Play in English](https://flessnerchernosky-ops.github.io/robot-delay-lab/arm/?lang=en)** · [中文试玩](https://flessnerchernosky-ops.github.io/robot-delay-lab/arm/)

The star looks close. Why can’t the arm catch it? Explore robot geometry, feedback, command delay and actuator limits in one browser experiment. Start by playing, then inspect the model and record your own findings. No hardware or installation is needed.

## A three-minute start

1. Watch Within reach. The coral arm uses position feedback; the green arm also brakes using joint velocity. Both share the target, initial state and actuator constraints.
2. Complete Overshooting, save the 12-second run, change only braking strength, and finish another run. The notebook checks whether exactly one setting changed.
3. Choose Late commands, set only delay to zero, and complete a comparison. PD braking commands are delayed too.
4. Drag the star beyond the reach ring or tighten joint limits. Stronger correction cannot overcome a geometric constraint.
5. Download the CSV and your Markdown notes. Up to 8 runs are stored only in the current page; refreshing or closing clears them.

Coordinate inputs provide keyboard access and select a fixed target. Orbit uses a fixed circular route and ignores coordinate inputs. Dragging changes both targets together. Free-play runs record target edits but are excluded from single-variable comparisons.

## Five challenges

| Challenge | Question |
|---|---|
| Within reach? | How do link lengths constrain the workspace? |
| Overshooting | What do position correction and velocity feedback contribute? |
| Late commands | What happens when braking arrives late? |
| Joint limits | Can a geometrically reachable target be blocked for this posture? |
| Moving star | How does tracking differ from approaching a fixed target? |

## Teaching model

Link lengths are `l1=1 m`, `l2=0.8 m`. With joint angles `q1,q2`:

```text
x = l1*cos(q1) + l2*cos(q1+q2)
y = l1*sin(q1) + l2*sin(q1+q2)
```

The geometric reach radius is `[0.2,1.8] m`. Inverse kinematics uses a fixed positive-elbow branch (`q2>=0`). Unreachable targets are projected to the radius boundary; angles outside joint limits are clamped. Controllers follow these reference angles, while scores always use the **actual star position**. The faint arm shows the clamped reference posture.

Default angle ranges are `q1∈[-π,π]`, `q2∈[0,π]`; tighter ranges are `q1∈[-1.4,1.4]`, `q2∈[0.15,2.7] rad`. A blocked selected branch does not prove the other elbow posture is unreachable. The other branch is not searched.

Each joint is an independent servo with unit equivalent inertia:

```text
q' = v
v' = u - 0.3*v
P : u_requested = Kp*(q_reference - q)
PD: u_requested = Kp*(q_reference - q) - Kd*v
```

Commands are clipped to `[-6,6]` (angular-acceleration input in rad/s² under the unit-inertia convention), then enter equal-length delay queues. Controllers observe current true state; there is no perception delay or noise. Queues initially contain zero inputs. Delays are integer multiples of 0.01 s: with a 0.35 s delay, the first command is applied on step 36.

Constant inputs use the exact viscous linear-system update. When velocity reaches its cap within a step, the crossing time is calculated and the remainder moves at the cap. Joint stops clamp angle and remove outward velocity. These are ideal hard constraints without contact forces or elastic collisions.

Initial state: `q=[-0.55,1.8] rad`, `v=[0,0] rad/s`. Each run has 1200 steps over 12 s. Orbit uses `x=1+0.3*cos(0.65*t)`, `y=0.65+0.3*sin(0.65*t)`. Control references sample the target at interval start; errors use the interval-end target. Neither controller reads a future target.

This model omits gravity, inertia matrices, joint coupling, collisions, grippers and contact. The star is a target position; catching is a distance test. P and PD are basic comparisons, not novel algorithms. There is no hardware validation.

## Reading the scores

- Whole-run RMSE: root mean square of 1200 endpoint distances, including approach, in meters.
- Last 4 seconds RMSE: 400 samples with timestamps `(8,12] s`. Displays `—` before reaching that interval.
- Nearby duration: number of samples within 0.06 m multiplied by the time step, a sampled approximation.
- First hold: earliest end time of 0.5 continuous seconds within the distance threshold; blank means no hold. It does not require zero velocity or guarantee later stability.
- Limit-step counts: summary data also records steps when either joint touches angle, speed or command limits.

CSV starts with `# arm-lab-v1` and JSON metadata: initial/final settings, time step, completion status, free-play flag and target edits. English column names follow. Each step has one row per method, with reference angles, actual angles/velocities, requested commands, applied inputs, target and error. Skip the metadata line in CSV readers, e.g. `pandas.read_csv(path, comment='#')`.

## Included results and reproduction

`examples/arm/summary.csv` contains 31 configuration entries / 62 deterministic trajectories. `manifest.json` stores full settings and metrics. Entries include five presets plus delay/gain, braking and speed sweeps. **Repeated baselines are included; these are not 31 distinct conditions or independent random trials.**

Baseline whole-run RMSE is approximately 0.169 m for P and 0.074 m for PD. Neither method achieves a hold in Late commands. In the braking sweep, PD with `Kd=4` has about 0.074 m RMSE, versus 0.091 m with `Kd=8`: stronger braking can increase error during approach. Findings apply only to the included model and settings, without statistical confidence intervals.

Requires Node.js; the independent check also requires Python 3.10+ standard library. No additional dependencies. From the repository root:

```text
node checks/arm.cjs
python verify_arm.py
node checks/arm_examples.cjs
```

15 checks cover geometry, reachability, delay, exact updates, speed caps, joint stops, metrics, sample refinement and notebook comparisons. Python independently constructs a sampled linear closed-loop recurrence and checks 2400 fixed-target, zero-delay, unsaturated rows. Maximum state discrepancy is approximately `3.5e-14`; this does not validate nonlinear constrained behavior or real robot dynamics.

Generate full example trajectories:

```text
node -e "const fs=require('node:fs'),E=require('./docs/arm/engine.js'),r=new E.Experiment(E.presets.delay);r.finish();fs.writeFileSync('arm-delay.csv',E.csv(r))"
```

You can also open `docs/arm/index.html` offline. The page needs no external fonts, scripts or backend. Experiment data is not uploaded.

## References and contributions

[PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) provides readable robotics algorithms; [Robotics Toolbox for Python](https://github.com/petercorke/robotics-toolbox-python) provides kinematics, dynamics and visualization tools. Their teaching approaches and public principles inform this module. This is an original simplified implementation, without copied upstream code or runtime dependencies on those projects.

Reproducible issues and improvements are welcome: include complete settings, CSV, expected/actual behavior and interface language. Possible extensions include branch continuity, richer dynamics and controller comparisons. New methods should share initial states, targets and constraints. MIT licensed and AI-assisted; contributors should understand and verify results and avoid describing this as a validated novel research algorithm.
