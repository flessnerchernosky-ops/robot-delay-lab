# 第一期 · 小车能沿路线走稳吗？

[中文](EPISODE_01.zh-CN.md) · [English](EPISODE_01.en.md) · [三期项目总览](https://flessnerchernosky-ops.github.io/robot-delay-lab/showcase.html?lang=zh)

**问题：转向指令迟到后，根据命令历史预测位置，一定能改善路径跟踪吗？**

![同一路线、同一转向延迟的两种控制器](docs/media/path-tracking.gif)

动画来自已保存的 v0.2 实验日志：S 形路线、1 m/s、0.5 秒转向延迟、1 m 前视距离。它展示一个例子；完整比较还包括预测退化的情况。

## 先看什么

1. 灰色虚线是路线，珊瑚色是普通 Pure Pursuit，绿色是预测状态 Pure Pursuit。
2. 两种控制器使用相同路线、初始状态、速度、实际延迟与控制约束。区别在于用于控制的状态估计。
3. 看整段实验的误差，而不是只选最漂亮的一瞬间。主要指标覆盖前 15 m 路线进度，不一定等于前 15 秒。

## 如何复现

下载仓库并进入根目录，建议 Python 3.12：

```text
python -m pip install -r requirements.txt
python study.py --out my_results
python linear_analysis.py --out my_results
python plot_study.py --results my_results --gif
python -m unittest -v
```

`my_results` 是新输出目录。已有 `results_v02/` 是 2026-10-09 的实验快照，方便核对。核心仿真使用标准库；绘图、谱分析与完整测试需要所列依赖。

完整设置在 [study_config.json](study_config.json)，轨迹设置在 [manifest.json](results_v02/manifest.json)，正反结果在 [paired_comparison.csv](results_v02/paired_comparison.csv)。已有 182 条确定性轨迹与 16 项 Python 检查。

## 做一个自己的实验

复制设置文件，先只改变前视距离。使用同一路线、速度和延迟，记录两种方法的误差、转向变化与评估窗口是否完成。先写猜测，再运行，最后解释结果。调参路线与评估路线应分开。

## 研究边界

这是二维运动学自行车模型：恒定速度，只延迟转向命令，读取当前真实状态。未模拟感知噪声、轮胎侧滑、碰撞或真实硬件。v0.2 使用恒定输入精确圆弧更新。

预测只使用当前状态和待执行命令；模型或延迟估计不准确时，可以变差。确定性重复不是独立随机实验，跨路线范围也不是统计置信区间。尚未证明算法新颖性。

继续阅读：[完整中文研究报告](REPORT_V02.md) · [局部稳定性分析](THEORY.md) · [仿真源码](study.py) · [贡献指南](CONTRIBUTING.md)。
