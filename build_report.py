"""Build the Chinese study report from saved CSV files; standard library only."""
import argparse
import csv
import json
import os
import statistics
from pathlib import Path
from simulate import ROOT


def read_csv(path):
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT/"results_v02")
    parser.add_argument("--out", type=Path, default=ROOT/"REPORT_V02.md")
    parser.add_argument("--date", default="2026-10-09", help="User-specified experiment date")
    args = parser.parse_args()
    rows = read_csv(args.results/"summary.csv")
    pairs = read_csv(args.results/"paired_comparison.csv")
    margins = read_csv(args.results/"linear_margins.csv")
    plan = json.loads((args.results/"plan_used.json").read_text())
    main_rows = [r for r in rows if r["group"] in ("comparison", "holdout")]
    nonzero = [p for p in pairs if float(p["delay_s"]) > 0 and p["both_windows_reached"] == "True"]
    gains = [float(p["rmse_improvement_percent"]) for p in nonzero]
    pp = [r for r in main_rows if r["controller"] == "pp"]
    predicted = [r for r in main_rows if r["controller"] == "predictor"]
    table = ["| 路线 | 普通 PP RMSE / m | 预测补偿 RMSE / m | 误差降幅 | 普通 PP 完成 | 补偿完成 |",
             "|---|---:|---:|---:|---|---|"]
    for p in pairs:
        if float(p["speed_m_s"]) == plan["study_speed"] and float(p["delay_s"]) == plan["sensitivity_delay"]:
            table.append(f"| {p['route']} | {float(p['pp_rmse_m']):.4f} | {float(p['predictor_rmse_m']):.4f} | {float(p['rmse_improvement_percent']):.1f}% | {'是' if p['pp_completed']=='True' else '否'} | {'是' if p['predictor_completed']=='True' else '否'} |")
    group_table = ["| 实验组 | 轨迹数 | 完成 15 m 评估范围 | 满足终点判定 |", "|---|---:|---:|---:|"]
    for group in ("comparison", "holdout", "lookahead", "delay_mismatch", "model_mismatch", "numerics"):
        selected = [r for r in rows if r["group"] == group]
        group_table.append(f"| {group} | {len(selected)} | {sum(r['evaluation_reached']=='True' for r in selected)} | {sum(r['completed']=='True' for r in selected)} |")
    margin_table = ["| 速度 / m·s⁻¹ | 连续局部边界 / s | 采样网格最后稳定 / s | 采样网格首个非稳定 / s |", "|---|---:|---:|---:|"]
    for row in margins:
        margin_table.append(f"| {float(row['speed_m_s']):g} | {float(row['continuous_local_boundary_s']):.4f} | {float(row['last_sampled_stable_delay_s']):.2f} | {float(row['first_sampled_nonstable_delay_s']):.2f} |")
    mismatch = [r for r in rows if r["group"] == "delay_mismatch" and r["route"] == "s_curve"]
    mismatch_table = ["| 假设延迟 / s | 实际延迟 / s | RMSE / m |", "|---|---|---:|"]
    for row in mismatch:
        mismatch_table.append(f"| {float(row['estimated_delay_s']):.1f} | {float(row['delay_s']):.1f} | {float(row['rmse_m']):.4f} |")
    text = f"""# Robot Delay Lab v0.2：适用条件与参数权衡

实验日期：{args.date}。本报告由保存的配置和 CSV 自动生成。研究问题：预测式转向延迟补偿何时有利，其效果如何受速度、前视距离、延迟估计和模型误差影响？

## 1. 本轮完成内容

完成 {len(rows)} 条仿真轨迹，分为以下六组；局部线性矩阵的谱分析单独保存，不算作机器人轨迹实验。

{chr(10).join(group_table)}

两种方法共用实际小车、速度、转向角限幅、路线和初始状态。主比较使用固定 {plan['base']['lookahead']:g} m 前视距离，不根据评估路线调整参数。

开发路线为 `{', '.join(plan['development_routes'])}`，额外路线为 `{', '.join(plan['holdout_routes'])}`。前视距离扫描仅使用开发路线。额外路线也出现在预先声明的模型敏感性诊断中，因此它们不是对所有研究决策永久封存的测试集。

核心计算不依赖 GPU。当前所有实验为确定性场景，没有加入随机测量噪声、通信抖动或实物验证。

## 2. 主比较与重要反例

主比较共 {len(pairs)} 对，普通 PP 有 {sum(r['completed']=='True' for r in pp)}/{len(pp)} 条轨迹满足终点判定，匹配预测补偿为 {sum(r['completed']=='True' for r in predicted)}/{len(predicted)}。这里是有限确定性场景的完成计数，不是实际机器人可靠性的统计估计。

非零延迟的 {len(nonzero)} 对实验中，预测补偿有 {sum(g>1e-6 for g in gains)} 对降低了主要 RMSE，{sum(g < -1e-6 for g in gains)} 对增加了 RMSE。全部非零延迟对的误差降幅中位数为 **{statistics.median(gains):.2f}%**；负值说明中位数情形下补偿更差。因此不能用大延迟案例的改善代表所有条件。

![不同速度下的比较](results_v02/controller_comparison.png)

下表固定速度 {plan['study_speed']:g} m/s、真实延迟 {plan['sensitivity_delay']:g} s、前视距离 {plan['base']['lookahead']:g} m，模型和延迟估计匹配：

{chr(10).join(table)}

![每组实验的降幅，包括负结果](results_v02/paired_improvement.png)

初始偏差和启动时尚未到达的指令会形成瞬态；精确预测不能消除启动等待。普通 PP 的有限延迟也可能改变该瞬态的形状，这可能影响包含起步阶段的整体 RMSE。当前数据只能支持现象描述，尚未通过严格分解解释每一个负结果。

`post_2m_rmse_m` 另行记录前 15 m 评估范围内、进度不小于 2 m 的误差。它是排除一部分起步阶段的诊断指标，未被用来替代主指标挑选更好看的结论。

## 3. 理论解释及其范围

连续直线路径、小误差、无限幅的局部模型推导得到 `tau_star ≈ 0.520494347 * lookahead / speed`。项目实际实现采样控制，因此另行使用零阶保持的离散增广矩阵计算谱半径。

{chr(10).join(margin_table)}

以上采样网格步长为 {plan['base']['dt']:g} s，边界对应直线局部模型，不能当作完整非线性小车的全局稳定或安全结论。饱和系统可能呈现有界振荡，轨迹振荡与无界发散不能混为一谈。

理想匹配预测器的增广线性模型，其特征值等于零延迟闭环的特征值加上队列移位产生的零特征值。在 `0 < speed * dt / lookahead < 1` 时，这个理想局部模型稳定。完整推导见 `THEORY.md`，并通过雅可比差分和谱一致性检查核对实现。

谱扫描还显示：普通 PP 在一些小正延迟下的谱半径比零延迟更小。这提供了瞬态响应变化的一条分析线索；但谱半径不能独自决定包含初始等待的有限时间 RMSE，仍需结合模态、初始条件和完整响应分析。

![局部谱半径](results_v02/local_stability.png)

## 4. 参数敏感性

前视距离并非越大越好：增大它可使普通 PP 在大延迟条件下更平稳，同时会改变跟踪响应及转弯误差。预测器也受前视距离影响。

![前视距离扫描](results_v02/lookahead_tradeoff.png)

该扫描表明，固定 1 m 的比较不能推出“预测器优于所有经过调参的普通 PP”。例如普通 PP 增大前视距离后，也可显著降低这组大延迟下的误差。当前没有在独立调参预算下比较两种方法的最优设置。

延迟估计误差以 `assumed_delay - actual_delay` 表示；控制器使用自己的命令历史，无法查看真实执行队列。S 形路线的敏感性结果如下：

{chr(10).join(mismatch_table)}

![延迟估计与轴距模型误差](results_v02/model_sensitivity.png)

模型失配实验同时使用估计轴距进行预测和生成转向指令。因此它测量的是整个基于估计模型的控制器变化，而不是仅改变预测模型的独立效应。当前没有证明这些误差范围内的鲁棒稳定性。

## 5. 数值与因果性检查

新增精确的恒定转向圆弧更新；主研究采用该更新。16 条数值诊断轨迹交叉比较 0.02/0.01 s 采样周期、201/401 个路线点和欧拉/精确区间更新。

在同一采样周期下，欧拉与精确更新的差异主要诊断积分近似误差；改变采样周期同时改变了反馈更新频率，所以不能全部归因于积分误差。增加路线点数主要诊断参考折线的近似误差。

在匹配模型且无扰动条件下，旧预测与后来状态的离线核对误差达到浮点舍入量级；这是因果队列实现的一致性检查，不是未知真实环境下预测准确性的证据。

本机已有 16 项自动检查通过，包括原有 5 项、精确圆弧运动、预测因果时序、零延迟一致性、匹配预测残差、失配残差、雅可比核对和理想预测谱一致性。检查不构成全局稳定性证明。

## 6. 可以陈述与仍待研究的内容

可以陈述：本项目实现了可复现的 Pure Pursuit 延迟实验及一个基于命令历史的预测补偿方法；在预先列出的模型、路线和参数下，完整记录了改善和退化案例，并提供局部模型推导。

仍待研究：噪声、通信抖动、观测延迟、执行器动态、公平调参后的比较、未知模型下的误差边界，以及相关工作的完整检索。

预测补偿和前视距离设计已有文献基础。当前工作的价值是实现、实验设计和理解，尚不能据此宣称一种新的控制算法或达到期刊发表标准。相关文献与方法区别见 `THEORY.md`。

## 7. 下一轮建议

1. 先复现一对大延迟和一对小延迟轨迹，分别解释“改善”和“退化”。
2. 检查调大前视距离的普通 PP 是否已经满足目标，避免把参数选择问题误写成算法创新。
3. 将“何时启用预测补偿”作为新假设，用新的速度、路线和初始误差条件验证，而不是在本轮数据上反复挑阈值。
4. 再加入同种子测量噪声及重复运行，报告分布和失败案例。

本项目与另一条“二阶系统采样安全控制”论文线不同：这里的轨迹实验和局部稳定分析不能替代该论文的区间安全及递归可行性验证。
"""
    figure_path = Path(os.path.relpath(args.results, args.out.parent)).as_posix()
    text = text.replace("](results_v02/", f"]({figure_path}/")
    args.out.write_text(text, encoding="utf-8")
    print(f"Report saved to {args.out}")


if __name__ == "__main__":
    main()
