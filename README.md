# HSR Action Axis Simulator - Python Version

这是一个 Python 版《崩坏：星穹铁道》行动轴仿真项目，功能对应之前的 MATLAB 版本，并额外支持 Streamlit 交互界面。

架构与仿真流程说明见 [FRAMEWORK.md](FRAMEWORK.md)。

## 功能

- 三角色行动轴仿真：花火、Archer、L
- 整数速度滑条
- 花火开局行动提前 40%
- 花火每次行动后给目标行动提前 50%
- 默认目标顺序：Archer / L 交替
- Archer 速度固定
- L 第一次行动后速度 +20
- 自动判定花火拉条是否浪费、每次浪费多少
- 自动判定 Archer 和 L 实际行动是否严格交替
- 交互式行动轴图
- 拉条浪费热力图
- 严格交替判定热力图，0/1 两种颜色显示
- 导出 Excel

## 推荐环境

使用 Anaconda Prompt：

```bash
conda create -n hsr-sim python=3.11 -y
conda activate hsr-sim
pip install -r requirements.txt
```

也可以用 conda-forge：

```bash
conda create -n hsr-sim python=3.11 -y
conda activate hsr-sim
conda install -c conda-forge numpy pandas plotly streamlit openpyxl -y
```

## 运行交互界面

进入项目文件夹后运行：

```bash
streamlit run app.py
```

浏览器会自动打开交互界面。

## 运行静态演示

```bash
python run_demo.py
```

会输出行动表、花火拉条表，并生成：

- `demo_action_axis.html`
- `demo_action_axis_separated.html`
- `demo_action_result.xlsx`

## 运行速度扫描

```bash
python speed_sweep.py
```

会生成：

- `speed_sweep_result.xlsx`
- `speed_sweep_waste_heatmap.html`
- `speed_sweep_alternation_heatmap.html`

## 修改花火逻辑

优先修改 `hsr_core.py` 里的：

```python
choose_sparkle_target(...)
```

目前支持：

```text
alternate
always_archer
always_l
min_progress
max_remaining_av
avoid_waste
```

默认是：

```text
alternate
```

## 文件说明

```text
FRAMEWORK.md            项目架构与仿真流程（框架梳理）
app.py                  Streamlit 交互界面
hsr_ui.py               数字参数输入（键盘 + 滚轮）
hsr_core.py             核心事件驱动仿真
hsr_plotting.py         Plotly 绘图函数
run_demo.py             非交互演示
speed_sweep.py          速度鲁棒性扫描
requirements.txt        pip 依赖
environment.yml         conda 环境文件
```
