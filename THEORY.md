# 延迟跟踪控制：从几何算法到局部稳定性

本说明针对项目的直线路径、小误差、恒定速度和未触发转向限幅的情形。曲线跟踪、较大初始误差、限幅和模型不确定性需要额外分析。以下内容是简化模型的推导与复现，尚未确认新的理论贡献。

## 1. Pure Pursuit 的局部线性化

记参考路径为 x 轴，横向偏差为 e，航向误差为 psi，沿路径的前视距离为 ell，轴距为 L，速度为 v。小车前方目标点在世界坐标系相对位置为 `(ell, -e)`。

转换到车体坐标系，目标点的横向位置为：

```text
y_local = -ell * sin(psi) - e * cos(psi)
```

在 `(e, psi) = (0, 0)` 附近：

```text
y_local ≈ -ell * psi - e
d² = ell² + e² ≈ ell²
curvature = 2 * y_local / d²
delta = atan(L * curvature) ≈ -2L/ell² * e - 2L/ell * psi
```

因此线性反馈为 `delta = K z`，其中：

```text
z = [e, psi]^T
K = [-2L/ell², -2L/ell]
```

这里的近似忽略了二阶及更高阶项，不适用于转向角饱和和大角度误差。

## 2. 连续时间、固定输入延迟的边界

若实际转向为 `delta(t - tau)`，线性化的运动方程是：

```text
e_dot(t)   = v * psi(t)
psi_dot(t) = v/L * delta(t - tau)

e_ddot(t) + 2v/ell * e_dot(t - tau) + 2v²/ell² * e(t - tau) = 0
```

特征方程：

```text
lambda² + exp(-lambda*tau) * (2v/ell * lambda + 2v²/ell²) = 0
```

引入无量纲变量 `s = lambda*ell/v` 和 `eta = tau*v/ell`：

```text
s² + exp(-s*eta) * (2s + 2) = 0
```

令虚轴上的根为 `s = j*omega`，比较两边模长得到：

```text
omega^4 = 4*omega² + 4
omega = sqrt(2 + 2*sqrt(2)) ≈ 2.19737
```

相位条件的第一组非负延迟解为：

```text
eta_star = atan(omega)/omega ≈ 0.520494347
tau_star = eta_star * ell/v
```

在 `eta = 0` 时根为 `-1 ± j`。零点不能成为特征根；非零虚轴交点只有上述频率以及其共轭，后续交点位于 `(atan(omega) + 2*pi*k)/omega`，k 为非负整数。

对特征方程隐式求导，在虚轴交点处：

```text
ds/deta = -s³ / [2s + 2exp(-s*eta) + eta*s²]
```

分母虚部为 `omega*(2 + omega²)/(1 + omega²) > 0`，分子为 `j*omega³`，因而穿越方向的实部为正：根从左半平面进入右半平面。

结合零延迟稳定性和滞后型线性系统的特征根连续性，连续时间的该局部线性模型在 `0 <= tau < tau_star` 时渐近稳定，在首个边界出现虚轴根。

**数值例子：** `v = 1 m/s, ell = 1 m` 时，连续模型第一边界约为 0.5205 s。这个值不是曲线路径、有限采样或转向限幅系统的全局临界值。

## 3. 仿真中真正实现的是采样控制

项目在每个采样周期 h 内保持速度和转向角不变。非线性模型使用圆弧运动的精确区间更新，因此无需通过更小积分步长近似一个采样周期。

若 `omega = v/L * tan(delta)`，用中点角和 sinc 函数可稳定计算更新：

```text
angle = omega*h
distance = v*h*sinc(angle/2), sinc(a) = sin(a)/a, sinc(0)=1
x_next = x + distance*cos(yaw + angle/2)
y_next = y + distance*sin(yaw + angle/2)
yaw_next = yaw + angle
```

线性化后的零阶保持离散模型为：

```text
z_next = A z + B delta_applied

A = [[1, v*h],
     [0,   1]]

B = [[v²*h²/(2L)],
     [v*h/L]]
```

对于 N 步延迟，将尚未生效的命令记作 `q_0 ... q_(N-1)`，其中 q_0 将在当前区间生效。增广状态是 `[z, q_0, ..., q_(N-1)]`。

普通 PP 的一步更新为：

```text
z_next = A z + B q_0
q_next = [q_1, ..., q_(N-1), K z]
```

`linear_analysis.py` 构造这个增广矩阵，并计算其谱半径 rho。`rho < 1` 对应该离散线性系统严格稳定；`rho > 1` 对应线性不稳定。谱半径约等于 1 时，需要留意数值容差。

采样边界来自整数延迟网格，报告中的“最后稳定值—第一个非稳定值”是一个网格区间，不是精确的连续延迟阈值。

## 4. 预测补偿如何保持因果性

时刻 k 新生成的指令 c_k 在 k+N 才生效。在这之前的 N 个区间，生效的都是已经生成的命令。因此，在模型和延迟完全已知、状态测量精确、无扰动时，可以计算：

```text
z_hat(k+N) = A^N z_k + sum_{j=0}^{N-1} A^(N-1-j) B q_j
c_k = K z_hat(k+N)
```

非线性实现则从当前测量状态开始，逐条滚动模拟控制器侧的历史命令。**预测器不读取真实小车的未来状态，也不读取真实执行队列。** 它有一个由估计延迟决定长度的独立命令历史队列。

若估计延迟与模型匹配，预测结果恰好等于该命令生效时的状态。真实轨迹在初始等待结束后满足同一个无延迟反馈更新，但开始反馈时的小车位置已受初始等待影响。所以补偿不能消除启动阶段的所有误差。

`max_prediction_position_residual_m` 是仿真结束后，将旧预测与后来发生的状态比较的诊断量；该诊断不会输入在线控制器。

## 5. 理想预测器的离散局部结论

令 `w = z_hat(k+N)`。由上述预测公式及队列更新，可以直接验证：

```text
w_next = (A + B K) w
q_next = shift(q) + last_column * K w
```

坐标变换 `[z, q] -> [w, q]` 可逆，因为 `A^N` 可逆。变换后矩阵为块下三角，两个对角块分别为 `A + B K` 和 N 阶移位矩阵 J。J 的所有特征值均为零。

所以理想预测增广系统的特征值为：

```text
eig(M_predictor) = eig(A + B K) union {N 个零}
```

再令 `a = v*h/ell`，对状态作尺度归一化后：

```text
A + B K ~ [[1-a², a-a²],
           [-2a,  1-2a]]

trace = 2 - 2a - a²
det   = (1-a)²
```

二阶 Jury 条件为：

```text
1-det > 0         -> a*(2-a) > 0
1-trace+det > 0   -> 2a² > 0
1+trace+det > 0   -> 4*(1-a) > 0
```

因此，理想匹配预测器的这个离散局部模型在 `0 < v*h/ell < 1` 时稳定，与整数延迟步数 N 无关。这个结论依赖精确预测，不覆盖估计误差、感知噪声、曲线路径或饱和非线性。

## 6. 如何核对实现与推导

1. 对增广非线性一步映射作中心差分，核对其在平衡点的雅可比是否等于推导的矩阵。
2. 核对不同 N 的匹配预测器谱半径是否与零延迟矩阵一致。
3. 核对已发出命令的实际时序，验证 N=0 与普通 PP 完全一致。
4. 将预测状态与实际 N 步之后状态作离线比较；匹配模型下应只剩浮点舍入量级的误差。

这些核对已写入自动检查。它们是实现一致性的证据，不能替代对完整非线性系统的证明。

## 7. 与已有研究的关系

- [Coulter, 1992：Pure Pursuit 的几何方法](https://publications.ri.cmu.edu/implementation-of-the-pure-pursuit-path-tracking-algorithm)。本项目使用该算法的几何思路。
- [Findeisen 等, 2011：预测式延迟补偿的鲁棒性](https://arxiv.org/abs/1105.3268)。这里用于说明预测补偿已有研究基础；论文中的控制序列结构和 ISS 假设不能直接当作本项目的稳定性证明。
- [Sukhil 与 Behl, 2021：自适应前视距离 Pure Pursuit](https://arxiv.org/abs/2111.08873)。它说明前视距离设计已有系统研究；本项目目前仅做固定参数扫描，没有复现该文的优化算法或实物实验。

后续需要进一步查阅本项目具体“命令队列预测 + Pure Pursuit”组合的已有工作，才能评估创新空间。
