# -*- coding: utf-8 -*-
"""
遗传算法优化 CTLE 眼图 - Qt 版（支持中文显示）
作者：AI助手
"""

import warnings

warnings.filterwarnings("ignore")

# ===== 设置 Matplotlib 后端和中文字体 =====
import matplotlib

matplotlib.use('Qt5Agg')  # 兼容 PySide2 / PyQt5


# 自动设置中文字体
def _setup_chinese_font():
    import matplotlib.font_manager as fm
    import platform

    system = platform.system()
    chinese_fonts = []

    if system == "Windows":
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'KaiTi', 'FangSong']
    elif system == "Darwin":  # macOS
        chinese_fonts = ['PingFang SC', 'STHeiti', 'Hiragino Sans GB', 'Arial Unicode MS']
    else:  # Linux
        chinese_fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback']

    for font in chinese_fonts:
        try:
            # 测试字体是否存在
            if font in [f.name for f in fm.fontManager.ttflist]:
                matplotlib.rcParams['font.family'] = font
                matplotlib.rcParams['axes.unicode_minus'] = False  # 正确显示负号
                print(f"✅ 已启用中文字体: {font}")
                return
        except Exception:
            continue

    # 备用方案：使用通用 sans-serif 并接受可能的方块（但至少不崩溃）
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Bitstream Vera Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    print("⚠️ 未找到理想中文字体，尝试使用后备字体")


_setup_chinese_font()

import matplotlib.pyplot as plt

# Qt 相关导入
from qtpy import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import sys
import os
import random
import numpy as np
import pandas as pd
import time
from pathlib import Path

# Keysight ADS 相关（请确保你有 keysight.edatoolbox）
try:
    from keysight.ads import de
    from keysight.ads.de import db_uu as db
    import keysight.ads.dataset as dataset
    from keysight.edatoolbox import ads
except ImportError as e:
    print(f"⚠️ Keysight ADS 模块未安装或不可用: {e}")
    sys.exit(1)

# ===================== 全局配置 =====================
pi = 3.141592653

# --- 修改为你自己的路径 ---
workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"
target_probe = "Eye_Probe1"

# CTLE 参数
gm = 35  # mS
cp = 87  # fF

# 遗传算法参数
POPULATION_SIZE = 20
GENERATIONS = 3
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8

# 频率范围 (GHz)
FZ_RANGE = (1, 12)
FP1_RANGE = (12, 24)
FP2_RANGE = (24, 48)

# 评分权重
WIDTH_WEIGHT = 0.3
ABS_HEIGHT_WEIGHT = 0.35
REL_HEIGHT_WEIGHT = 0.35

# 归一化上限
MAX_EYE_WIDTH_PS = 20.0
MAX_ABS_EYE_HEIGHT_V = 1.0


# ===================== 工具函数 =====================
def UCIe(gm, cp, zero_list, poles_list):
    wz_val = eval(zero_list[0])
    wp1_val = eval(poles_list[0])
    wp2_val = eval(poles_list[1])
    gm_S = gm * 1e-3
    cp_F = cp * 1e-15
    Aac = gm_S / (cp_F * wp2_val)
    Adc = (wz_val * Aac) / wp1_val
    Apre = (Adc * wp1_val * wp2_val) / wz_val
    return f"{Apre:.6f}"


def simulate_eye(fz, fp1, fp2, gm=gm, cp=cp):
    zero = [f"(-{fz}e9)*(2*pi)"]
    poles = [f"(-{fp1}e9)*(2*pi)", f"(-{fp2}e9)*(2*pi)"]
    Apre = UCIe(gm, cp, zero, poles)

    try:
        design = db.open_design(name=(library_name, cell_name, "schematic"))
        rx_diff1 = design.find_instance("Rx_Diff1")
        rx_diff1.parameters['Gain'].value = Apre
        rx_diff1.parameters['Zero'].value = zero
        rx_diff1.parameters['Pole'].value = poles
        rx_diff1.update_item_annotation()

        netlist = design.generate_netlist()
        simulator = ads.CircuitSimulator()
        target_output_dir = os.path.join(workspace_path, r"data/python_data")
        os.makedirs(target_output_dir, exist_ok=True)
        simulator.run_netlist(netlist, output_dir=target_output_dir)

        ds_path = Path(os.path.join(target_output_dir, f"{cell_name}.ds"))
        output_data = dataset.open(ds_path)

        # 查找眼高测量块
        eye_meas_block = None
        for datablock in output_data.find_varblocks_with_var_name("Height"):
            if target_probe in datablock.name:
                eye_meas_block = datablock.name
                break
        if not eye_meas_block:
            raise ValueError("未找到眼图测量块")

        my_eye_meas = output_data[eye_meas_block].to_dataframe().reset_index()
        height = my_eye_meas["Height"].iloc[0]
        width_s = my_eye_meas["Width"].iloc[0]
        width_ps = width_s * 1e12
        level1 = my_eye_meas["Level1"].iloc[0]
        level0 = my_eye_meas["Level0"].iloc[0]

        # 查找原始眼图数据
        eye_raw_block = None
        for datablock in output_data.find_varblocks_with_var_name("Density"):
            if target_probe in datablock.name:
                eye_raw_block = datablock.name
                break
        if not eye_raw_block:
            raise ValueError("未找到眼图原始数据块")

        my_eye_raw = output_data[eye_raw_block].to_dataframe().reset_index()
        df_raw = pd.DataFrame({
            "索引": my_eye_raw["index"],
            "时间(s)": my_eye_raw["time"],
            "时间(ps)": my_eye_raw["time"] * 1e12,
            "电压(V)": my_eye_raw["Density"]
        })

        raw_csv_filename = os.path.join(target_output_dir, f"{target_probe}_眼图原始数据.csv")
        df_raw.to_csv(raw_csv_filename, index=False, encoding="utf-8-sig")
        return height, width_ps, level1, level0

    except Exception as e:
        main_window.log_message(f"⚠️ 仿真出错：{e}")
        return 0.0, 0.0, 0.0, 0.0


def plot_eye_heatmap_to_ax(ax, df, title):
    time_ps = df["时间(ps)"].values
    voltage_v = df["电压(V)"].values

    time_range = time_ps.max() - time_ps.min()
    voltage_range = voltage_v.max() - voltage_v.min()
    time_bins = max(100, int(time_range * 5))
    voltage_bins = max(50, int(voltage_range * 200))

    heatmap, xedges, yedges = np.histogram2d(
        time_ps, voltage_v,
        bins=[time_bins, voltage_bins],
        density=False
    )
    heatmap = heatmap.T

    ax.clear()
    ax.imshow(
        heatmap,
        extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
        origin='lower',
        aspect='auto',
        cmap='viridis',
        interpolation='bilinear'
    )
    ax.set_xlabel('时间 (ps)')
    ax.set_ylabel('电压 (V)')
    ax.set_title(title, fontsize=10)
    ax.grid(False)


def fitness_function(fz, fp1, fp2):
    height, width_ps, level1, level0 = simulate_eye(fz, fp1, fp2)
    swing = level1 - level0
    if swing <= 0:
        swing = 1e-6

    norm_width = min(width_ps / MAX_EYE_WIDTH_PS, 1.0)
    norm_abs_height = min(height / MAX_ABS_EYE_HEIGHT_V, 1.0)
    norm_rel_height = min(height / swing, 1.0)

    score = (
            WIDTH_WEIGHT * norm_width +
            ABS_HEIGHT_WEIGHT * norm_abs_height +
            REL_HEIGHT_WEIGHT * norm_rel_height
    )
    return max(0.0, min(score, 1.0)), height, width_ps, level1, level0


# ===================== 遗传算法核心 =====================
def initialize_population():
    return [(random.uniform(*FZ_RANGE), random.uniform(*FP1_RANGE), random.uniform(*FP2_RANGE)) for _ in
            range(POPULATION_SIZE)]


def select(population):
    scores = [fitness_function(*ind)[0] for ind in population]
    total = sum(scores)
    if total == 0:
        return random.choices(population, k=POPULATION_SIZE)
    probs = [s / total for s in scores]
    return random.choices(population, weights=probs, k=POPULATION_SIZE)


def crossover(p1, p2):
    if random.random() < CROSSOVER_RATE:
        pt = random.randint(0, 2)
        c1 = list(p1);
        c2 = list(p2)
        c1[pt:], c2[pt:] = p2[pt:], p1[pt:]
        return tuple(c1), tuple(c2)
    return p1, p2


def mutate(ind):
    fz, fp1, fp2 = ind
    if random.random() < MUTATION_RATE:
        fz = max(FZ_RANGE[0], min(FZ_RANGE[1], fz + random.uniform(-0.5, 0.5)))
    if random.random() < MUTATION_RATE:
        fp1 = max(FP1_RANGE[0], min(FP1_RANGE[1], fp1 + random.uniform(-1, 1)))
    if random.random() < MUTATION_RATE:
        fp2 = max(FP2_RANGE[0], min(FP2_RANGE[1], fp2 + random.uniform(-2, 2)))
    return (fz, fp1, fp2)


# ===================== Qt 主窗口 =====================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("遗传算法优化眼图 - Qt 版")
        self.resize(900, 700)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Matplotlib 画布
        self.fig = Figure(figsize=(8, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # 日志框
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Consolas")  # 日志用等宽英文字体，避免混排问题
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # 开始按钮
        self.start_btn = QtWidgets.QPushButton("开始优化（3代）")
        self.start_btn.clicked.connect(self.start_optimization)
        layout.addWidget(self.start_btn)

        self.log_message("✅ 环境检测通过：QtPy + PySide2 + Matplotlib(Qt5Agg)")
        self.log_message("✅ 中文字体已自动配置")
        self.log_message("点击“开始优化”运行遗传算法...")

    def log_message(self, msg):
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        QtWidgets.QApplication.processEvents()

    def start_optimization(self):
        self.start_btn.setEnabled(False)
        self.run_genetic_algorithm()

    def run_genetic_algorithm(self):
        global main_window
        main_window = self

        self.log_message("\n=== 开始遗传算法优化 ===")
        de.open_workspace(workspace_path)

        population = initialize_population()
        best_ind, best_score = None, 0
        best_h, best_w, best_l1, best_l0 = 0, 0, 0, 0

        target_output_dir = os.path.join(workspace_path, r"data/python_data")
        raw_csv = os.path.join(target_output_dir, f"{target_probe}_眼图原始数据.csv")

        ga_start = time.time()

        for gen in range(GENERATIONS):
            self.log_message(f"\n--- 第 {gen + 1} 代 ---")
            gen_scores = []

            for ind in population:
                score, h, w, l1, l0 = fitness_function(*ind)
                gen_scores.append((score, ind, h, w, l1, l0))
                if score > best_score:
                    best_score, best_ind = score, ind
                    best_h, best_w, best_l1, best_l0 = h, w, l1, l0

            gen_scores.sort(reverse=True)
            top_score, top_ind, top_h, top_w, top_l1, top_l0 = gen_scores[0]
            fz, fp1, fp2 = top_ind
            swing = top_l1 - top_l0
            rel_ratio = top_h / swing if swing > 0 else 0

            self.log_message(f"最优: 零点={fz:.2f}GHz, 极点1={fp1:.2f}GHz, 极点2={fp2:.2f}GHz")
            self.log_message(f"眼高={top_h:.4f}V, 眼宽={top_w:.2f}ps, 摆幅={swing:.4f}V")
            self.log_message(f"得分={top_score:.4f}")

            # 更新图形
            simulate_eye(fz, fp1, fp2)
            try:
                df = pd.read_csv(raw_csv, encoding="utf-8-sig")
                plot_eye_heatmap_to_ax(
                    self.ax, df,
                    f'第 {gen + 1} 代最优眼图\n零点={fz:.2f}GHz, 极点1={fp1:.2f}GHz, 极点2={fp2:.2f}GHz'
                )
                self.canvas.draw()
            except Exception as e:
                self.log_message(f"⚠️ 绘图失败: {e}")

            # 遗传操作
            selected = select(population)
            next_pop = []
            for i in range(0, POPULATION_SIZE, 2):
                p1 = selected[i]
                p2 = selected[i + 1] if i + 1 < POPULATION_SIZE else selected[0]
                c1, c2 = crossover(p1, p2)
                next_pop.extend([c1, c2])
            population = [mutate(ind) for ind in next_pop[:POPULATION_SIZE]]

        # 最终结果
        ga_time = time.time() - ga_start
        self.log_message(f"\n✅ 优化完成！耗时 {ga_time:.2f} 秒")
        self.log_message(f"最终参数: 零点={best_ind[0]:.2f}GHz, 极点1={best_ind[1]:.2f}GHz, 极点2={best_ind[2]:.2f}GHz")

        # 保存最终图
        simulate_eye(*best_ind)
        df = pd.read_csv(raw_csv, encoding="utf-8-sig")
        final_fig, final_ax = plt.subplots(figsize=(6, 4))
        plot_eye_heatmap_to_ax(final_ax, df, "最终最优眼图")
        final_path = os.path.join(target_output_dir, "best_eye_diagram_heatmap.png")
        final_fig.savefig(final_path, dpi=200, bbox_inches='tight')
        plt.close(final_fig)
        self.log_message(f"✅ 最终眼图已保存至：{final_path}")


# ===================== 主程序入口 =====================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())