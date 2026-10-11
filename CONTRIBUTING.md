# Contributing · 参与贡献

Thanks for trying Robot Delay Lab. Small, evidence-based improvements are welcome.

感谢试玩 Robot Delay Lab。欢迎提出有依据、范围清楚的小改进。

## Start with a small task · 从小任务开始

| Task / 任务 | What a useful contribution includes / 完成标准 |
|---|---|
| Improve touch or keyboard access / 改善触控或键盘操作 | Describe the device and steps; verify drag, pause and controls still work. / 写明设备和复现步骤，确认拖动、暂停与控制面板正常。 |
| Improve Chinese or English copy / 优化中英文文案 | Update the corresponding language, keep model assumptions and metric meanings consistent. / 对应修改两种语言，保持模型假设与指标含义一致。 |
| Add a controlled learning example / 增加对照学习案例 | Use the same target and one changed parameter, keep complete-run settings and scores, include a limitation. / 保持同一目标、只改一项参数，记录完整设置与成绩并说明局限。 |

If you find a bug, open an Issue with the episode, browser/device, exact steps, expected/observed behavior and a screenshot or CSV if helpful. Avoid uploading passwords, tokens or private personal data.

发现问题时，请在 Issue 中写明期数、浏览器与设备、步骤、预期和实际现象；必要时附截图或 CSV。请勿上传密码、令牌或私人信息。

Before substantial model changes, explain the intended experiment and assumptions in an Issue. UI changes should preserve current runs and notes when switching language. Use `textContent` for user notes, not HTML insertion. Both browser engines also run in Node; keep that compatibility.

修改模型前，先说明实验目的与假设。语言切换应保留当前运行与个人笔记；用户文字使用 `textContent`，避免当作 HTML。浏览器引擎也在 Node 中运行，请保留兼容性。

## Check your change · 验证修改

Run the checks relevant to the episode from the repository root:

在仓库根目录运行与改动相关的检查：

```text
python -m pip install -r requirements.txt
python -m unittest -v
node checks/star_lab.cjs
node checks/notebook.cjs
node checks/arm.cjs
python verify_arm.py
node checks/arm_benchmark.cjs
```

For UI changes, also test Chinese / English, a narrow mobile viewport, pause/restart, and the relevant downloads. Do not overwrite the included study snapshots when trying a new experiment; use a separate output directory.

修改界面时，请检查中英切换、手机窄屏、暂停与重来，以及相关下载。新实验使用单独输出目录，保留已有研究快照。

Showcase media can be regenerated with Node.js and Pillow:

展示素材可用 Node.js 与 Pillow 重新生成：

```text
python -m pip install Pillow
python build_showcase.py
```

This reads included path-tracking logs and the current browser engines. Fonts may vary across platforms. The media are recorded simulation outputs, not hardware footage.

该脚本读取路径跟踪日志和浏览器引擎；不同平台的字体渲染可能不同。动图是仿真输出，不是实物录像。

Contributions use the repository's MIT license. Credit external sources and retain required licenses. Distinguish presets, experiments you performed, and AI assistance; do not claim unverified algorithm novelty or hardware performance.

贡献沿用 MIT 许可。引入外部内容时注明来源并保留所需许可；区分预设、亲自完成的实验与 AI 协助，不宣称未经验证的算法创新或硬件性能。
