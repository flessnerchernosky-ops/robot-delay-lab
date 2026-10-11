# Episode 2 · Don’t overshoot: Star Chase Lab

[中文](EPISODE_02.md) · [English](EPISODE_02.en.md) · [Explore all episodes](https://flessnerchernosky-ops.github.io/robot-delay-lab/showcase.html?lang=en)

**Why can chasing harder make a spacecraft wobble more?** No control theory, programming or hardware is needed to start.

**[Play in English](https://flessnerchernosky-ops.github.io/robot-delay-lab/?lang=en)** · [Scores](examples/star_chase_summary.csv) · [Model source](docs/engine.js)

![Actual spacecraft model output: the more-wobble preset](docs/media/star-chase.gif)

## A three-minute start

1. **Gentle approach:** all automatic methods coincide with zero delay. Reaching the star quickly does not guarantee stopping there.
2. **More push, more wobble:** commands arrive 0.4 s late. Watch the coral spacecraft overshoot repeatedly. Off-screen positions are displayed; the physics does not clamp them back into view.
3. **Learn to brake:** only braking differs from the previous preset. Compare complete-run errors.
4. **Moving star:** the predictor assumes constant target velocity for the waiting interval. Turns challenge that assumption.
5. **Prediction can fail:** fast reversals provide a counterexample. Complete the 20-second run before judging the purple spacecraft.

Enable **Let me fly too** and hold Left / Right or A / D or the arrow keys. Releasing stops thrust, not motion. Your commands also have the configured delay. Touch controls work on phones. Dragging the flight area changes the target; restart after a run ends.

## Feedback, delay and prediction

Feedback chooses thrust using current position error and velocity. Delay puts thrust commands in a queue while old commands keep executing. Prediction advances the current state through pending commands to estimate where the spacecraft will be when a new command takes effect.

The predictor reads only the target’s **current position and velocity**, assumes constant velocity during the wait and clamps the estimated target to its allowed range. It never calls a future-target function or knows your next drag. Sudden changes can defeat the estimate.

## Reference scores

Snapshot: 2026-10-10. Each run starts from the same state and lasts 2400 steps / 20 seconds. Values are whole-run RMSE in simulation units, including the initial approach.

| Preset | Instant | Delayed | Predictive |
|---|---:|---:|---:|
| Gentle approach | 0.553 | 0.553 | 0.553 |
| More push, more wobble | 0.574 | 6.024 | 0.714 |
| Learn to brake | 0.522 | 0.894 | 0.673 |
| Moving star | 0.645 | 3.047 | 0.810 |
| Prediction can fail | 1.021 | 0.886 | 1.181 |

In the final preset, predictive RMSE is about 33.3% higher than delayed RMSE. These selected teaching examples do not prove any method is universally better. Instant response is a **zero-delay reference**, not an equally delayed competitor.

## Keep your own evidence

Follow the [15-minute learning path](LEARNING_MISSIONS.en.md). Write a question and hypothesis, complete a run, explain it, then save the scores. Up to 12 snapshots stay in the current page; refreshing or closing clears them. Saved notes do not change when you later edit input fields. Download Markdown before leaving.

The notebook stores score summaries; download each full CSV separately. CSV includes elapsed time, parameters, target state and each spacecraft’s position, velocity, calculated and applied thrust. A partial CSV is not a complete-run comparison.

The comparison tool requires the same automatic target, manual driving off and no more than one parameter changed. Dragging or manual inputs can be recorded but are not controlled parameter comparisons.

## Offline and reproducible

Download the repository ZIP, extract it, and open `docs/index.html?lang=en` via a local server, or open `docs/index.html` and click English. Keep `engine.js`, `notebook.js`, `i18n.js`, `app.js` and `style.css` together. Browsing HTML source on GitHub does not run the page.

Using Node.js from the repository root:

```text
node checks/star_lab.cjs
node checks/notebook.cjs
node checks/star_examples.cjs
```

The first two run 10 model checks and 4 notebook checks; the last regenerates the examples. Node.js is not required to play.

## Model and limits

This fictional one-dimensional system has position and velocity, bounded thrust ±6 and drag 0.15. Constant-input steps use an analytical update at 1/120 s. Delay is rounded to integer steps. Positions have no hard boundary; the visible −4 to +4 range and auto-scaled plot are display choices.

Automatic thrust is position gain × position error − braking coefficient × velocity, with braking coefficient `2 × damping × sqrt(gain)`. Instant and delayed methods use the same formula. Prediction changes the control state estimate using pending commands.

Rows describe interval endpoints; target columns contain the command held during that interval. All automatic methods share parameters, except the reference has zero command delay. The model has no hardware validation, noise, perception delay, real spacecraft dynamics or claim of a new algorithm. MIT licensed and AI-assisted.
