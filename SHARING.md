# Share Robot Delay Lab · 分享项目

These drafts are ready to adapt, but have not been posted to social platforms. Keep the scope accurate and follow each community's sharing rules.

下面是可按需修改的介绍文案，尚未发布到社交平台。请保持事实准确，并遵守目标社区的分享规则。

## 中文介绍

**为什么越努力纠正，反而越容易追过头？**

我在整理一个无需硬件的开源机器人控制学习项目：Robot Delay Lab。目前有三期——小车路径跟踪、太空追星和机械臂抓星星。

后两期打开浏览器就能玩，支持中英文与手机：调延迟和刹车、拖动目标，观察预测什么时候有用、什么时候猜错；还可以下载实验数据和自己的笔记。第一期提供 Python 复现、参数敏感性与局部稳定性分析。

这些是简化教学与研究模型，由 AI 协助制作，尚未进行真实硬件验证。欢迎试玩、反馈问题，或分享你发现的一个反例。觉得有用的话，也欢迎 Star 收藏。

试玩：https://flessnerchernosky-ops.github.io/robot-delay-lab/showcase.html?lang=zh

源码：https://github.com/flessnerchernosky-ops/robot-delay-lab

## English introduction

**Why can trying harder make you overshoot?**

I’m building Robot Delay Lab, an open-source, hardware-free control learning project with three episodes: robot path tracking, Star Chase and Catch the Stars.

The last two run directly in a browser, with Chinese/English UI and mobile support. Tune command delay and braking, drag a target, discover when prediction helps or fails, and export trajectories and your own notes. The first episode offers a reproducible Python study, parameter sensitivity and local stability analysis.

These are simplified teaching and study models, built with AI assistance and without real hardware validation. Try them, report a problem, or share a counterexample you found. If useful, star the repository to keep it handy.

Play: https://flessnerchernosky-ops.github.io/robot-delay-lab/showcase.html?lang=en

Source: https://github.com/flessnerchernosky-ops/robot-delay-lab

## Media · 素材

- [Repository sharing card / 仓库分享封面](docs/media/social-preview.png): 1280×640, under 1 MB.
- [Path tracking / 路径跟踪](docs/media/path-tracking.gif): 15-second recorded S-curve case; not the full evaluation window.
- [Star Chase / 太空追星](docs/media/star-chase.gif): the 20-second more-wobble preset.
- [Catch the Stars / 机械臂](docs/media/catch-the-stars.gif): the 12-second overshoot preset.
- [Generation settings / 生成设置](docs/media/manifest.json) and [reproduction script / 复现脚本](build_showcase.py).

Prefer showing one question and its observable result in a short demonstration. Link to the interactive page and repository; distinguish simulation from hardware and a selected example from a general conclusion.

短演示建议只讲一个问题与可观察的结果，同时提供试玩与源码链接。区分仿真与实物，也区分选定案例和普遍结论。
