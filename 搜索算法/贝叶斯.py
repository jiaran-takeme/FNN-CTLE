# -*- coding: utf-8 -*-
"""
贝叶斯优化 CTLE 眼图 - Qt 版（支持中文显示）
✅ 所有输出保存至脚本同目录下的 Data/ 文件夹
✅ 修改逻辑：只要评分是目前最高的，就立即更新眼图
"""

import warnings

warnings.filterwarnings("ignore")

# ===== 设置 Matplotlib 后端和中文字体 =====
import matplotlib

matplotlib.use('Qt5Agg')


def _setup_chinese_font():
    import matplotlib.font_manager as fm
    import platform
    system = platform.system()
    chinese_fonts = []
    if system == "Windows":
        chinese_fonts = ['SimHei', 'Microsoft YaHei']
    elif system == "Darwin":
        chinese_fonts = ['PingFang SC', 'STHeiti']
    else:
        chinese_fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC']

    for font in chinese_fonts:
        try:
            if font in [f.name for f in fm.fontManager.ttflist]:
                matplotlib.rcParams['font.family'] = font
                matplotlib.rcParams['axes.unicode_minus'] = False
                print(f"✅ 已启用中文字体: {font}")
                return
        except Exception:
            continue
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False
    print("⚠️ 使用后备中文字体")


_setup_chinese_font()

import matplotlib.pyplot as plt

# Qt 相关导入
from qtpy import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import sys
import os
import numpy as np
import pandas as pd
import time
from pathlib import Path

# Keysight ADS 相关
try:
    from keysight.ads import de
    from keysight.ads.de import db_uu as db
    import keysight.ads.dataset as dataset
    from keysight.edatoolbox import ads
except ImportError as e:
    print(f"⚠️ Keysight ADS 模块未安装或不可用: {e}")
    sys.exit(1)

# ===================== 全局配置 =====================
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder_path = os.path.join(script_dir, "Data")
os.makedirs(data_folder_path, exist_ok=True)  # 自动创建 Data 文件夹

workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"
target_probe = "Eye_Probe1"
pi = 3.141592653
gm = 35  # mS
cp = 87  # fF

# 贝叶斯优化参数
N_CALLS = 50  # 总仿真次数
N_RANDOM_STARTS = 10  # 初始随机探索次数

# 参数范围 (GHz)
FZ_RANGE = (1, 12)
FP1_RANGE = (12, 24)
FP2_RANGE = (24, 48)

# 评分权重
WIDTH_WEIGHT = 0.2
ABS_HEIGHT_WEIGHT = 0.5
REL_HEIGHT_WEIGHT = 0.3

MAX_EYE_WIDTH_PS = 15
MAX_ABS_EYE_HEIGHT_V = 0.5

# 日志文件路径
log_file_path = os.path.join(data_folder_path, "optimization_log.txt")


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
        target_output_dir = data_folder_path
        os.makedirs(target_output_dir, exist_ok=True)
        simulator.run_netlist(netlist, output_dir=target_output_dir)

        ds_path = Path(os.path.join(target_output_dir, f"{cell_name}.ds"))
        output_data = dataset.open(ds_path)

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

        raw_csv_filename = os.path.join(data_folder_path, f"{target_probe}_眼图原始数据.csv")
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
    """返回负得分（因为 skopt 是最小化）"""
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
    score = max(0.0, min(score, 1.0))
    return -score, height, width_ps, level1, level0


# ===================== 贝叶斯优化核心 =====================
from skopt import gp_minimize
from skopt.space import Real

dimensions = [
    Real(FZ_RANGE[0], FZ_RANGE[1], name='fz'),
    Real(FP1_RANGE[0], FP1_RANGE[1], name='fp1'),
    Real(FP2_RANGE[0], FP2_RANGE[1], name='fp2')
]

current_best_score = -float('inf')  # 初始化为负无穷，确保第一次即更新
current_best_params = None
eval_count = 0
all_evaluations = []  # 存储所有评估记录


def objective(params):
    global current_best_score, current_best_params, eval_count, all_evaluations
    fz, fp1, fp2 = params
    neg_score, h, w, l1, l0 = fitness_function(fz, fp1, fp2)
    score = -neg_score

    eval_count += 1
    swing = l1 - l0
    rel_ratio = h / swing if swing > 0 else 0

    # 判断是否为新的最佳得分
    is_new_best = False
    if score > current_best_score:
        current_best_score = score
        current_best_params = (fz, fp1, fp2, h, w, l1, l0)
        is_new_best = True

    # 记录本次评估
    record = {
        "eval": eval_count,
        "fz_GHz": fz,
        "fp1_GHz": fp1,
        "fp2_GHz": fp2,
        "eye_height_V": h,
        "eye_width_ps": w,
        "level1_V": l1,
        "level0_V": l0,
        "swing_V": swing,
        "score": score
    }
    all_evaluations.append(record)

    # 日志到 UI 和文件
    msg = (
        f"[{eval_count}/{N_CALLS}] fz={fz:.2f}, fp1={fp1:.2f}, fp2={fp2:.2f} "
        f"| 眼高={h:.4f}V, 眼宽={w:.2f}ps, 得分={score:.4f}"
    )
    main_window.log_message(msg)
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

    # 🔥 关键修改：只要是最优解，就立即更新眼图
    if is_new_best:
        raw_csv = os.path.join(data_folder_path, f"{target_probe}_眼图原始数据.csv")
        try:
            df = pd.read_csv(raw_csv, encoding="utf-8-sig")
            plot_eye_heatmap_to_ax(
                main_window.ax, df,
                f'【新最优】第 {eval_count} 次评估\n零点={fz:.2f}GHz, 极点1={fp1:.2f}GHz, 极点2={fp2:.2f}GHz'
            )
            main_window.canvas.draw()
        except Exception as e:
            main_window.log_message(f"绘图失败: {e}")

    return neg_score


# ===================== Qt 主窗口 =====================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("贝叶斯优化眼图 - Qt 版（数据存于 ./Data）")
        self.resize(900, 700)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        self.fig = Figure(figsize=(8, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Consolas")
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        self.start_btn = QtWidgets.QPushButton("开始贝叶斯优化")
        self.start_btn.clicked.connect(self.start_optimization)
        layout.addWidget(self.start_btn)

        self.log_message("✅ 环境检测通过：QtPy + PySide2 + Matplotlib(Qt5Agg)")
        self.log_message("✅ 中文字体已配置")
        self.log_message("✅ 所有输出将保存至脚本同目录下的 Data/ 文件夹")
        self.log_message("点击“开始贝叶斯优化”运行...")

    def log_message(self, msg):
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        QtWidgets.QApplication.processEvents()

    def start_optimization(self):
        self.start_btn.setEnabled(False)
        self.run_bayesian_optimization()

    def run_bayesian_optimization(self):
        global main_window, current_best_score, current_best_params, eval_count, all_evaluations
        main_window = self
        current_best_score = -float('inf')
        current_best_params = None
        eval_count = 0
        all_evaluations = []

        # 清空旧日志
        open(log_file_path, "w", encoding="utf-8").close()

        self.log_message(f"\n=== 开始贝叶斯优化（共 {N_CALLS} 次仿真）===")
        de.open_workspace(workspace_path)

        start_time = time.time()

        result = gp_minimize(
            func=objective,
            dimensions=dimensions,
            n_calls=N_CALLS,
            n_random_starts=N_RANDOM_STARTS,
            random_state=42,
            verbose=False
        )

        total_time = time.time() - start_time

        # 保存完整评估记录为 CSV
        eval_df = pd.DataFrame(all_evaluations)
        eval_csv_path = os.path.join(data_folder_path, "optimization_history.csv")
        eval_df.to_csv(eval_csv_path, index=False, encoding="utf-8-sig")

        # 输出最终结果
        fz, fp1, fp2 = result.x
        best_score = -result.fun
        _, h, w, l1, l0 = fitness_function(fz, fp1, fp2)

        self.log_message(f"\n✅ 贝叶斯优化完成！耗时 {total_time:.2f} 秒")
        self.log_message(f"最优参数: 零点={fz:.2f}GHz, 极点1={fp1:.2f}GHz, 极点2={fp2:.2f}GHz")
        self.log_message(f"眼高={h:.4f}V, 眼宽={w:.2f}ps, 得分={best_score:.4f}")

        # 保存最终眼图
        simulate_eye(fz, fp1, fp2)
        raw_csv = os.path.join(data_folder_path, f"{target_probe}_眼图原始数据.csv")
        df = pd.read_csv(raw_csv, encoding="utf-8-sig")
        final_fig, final_ax = plt.subplots(figsize=(6, 4))
        plot_eye_heatmap_to_ax(final_ax, df, "贝叶斯优化 - 最终最优眼图")
        final_path = os.path.join(data_folder_path, "bayes_best_eye_diagram.png")
        final_fig.savefig(final_path, dpi=200, bbox_inches='tight')
        plt.close(final_fig)
        self.log_message(f"✅ 所有数据已保存至：{data_folder_path}")


# ===================== 主程序入口 =====================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())