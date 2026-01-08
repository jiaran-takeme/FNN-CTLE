import warnings

warnings.filterwarnings("ignore")
from keysight.ads import de
from keysight.ads.de import db_uu as db
import os
from keysight.edatoolbox import ads
import keysight.ads.dataset as dataset
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import random
import numpy as np
import time

# ===================== 全局配置 =====================
pi = 3.141592653

workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"
target_probe = "Eye_Probe1"
gm = 35  # mS
cp = 87  # fF

# 遗传算法参数
POPULATION_SIZE = 20
GENERATIONS = 3  # ✅ 3 代
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8

FZ_RANGE = (1, 12)  # GHz
FP1_RANGE = (12, 24)  # GHz
FP2_RANGE = (24, 48)  # GHz

# ✅ 三部分权重
WIDTH_WEIGHT = 0.3
ABS_HEIGHT_WEIGHT = 0.35
REL_HEIGHT_WEIGHT = 0.35

# 归一化参考值
MAX_EYE_WIDTH_PS = 20.0  # 最大合理眼宽（ps）
MAX_ABS_EYE_HEIGHT_V = 1.0  # 绝对眼高参考（V）


# ===================== 核心函数 =====================
def UCIe(gm, cp, zero_list, poles_list):
    global pi
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
    """执行ADS仿真，返回 eye_height, eye_width_ps, level1, level0"""
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

        # 提取眼图测量块（含 Height, Width, Level1, Level0）
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

        # 提取原始眼图数据（用于绘图）
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
        print(f"仿真出错：{e}")
        return 0.0, 0.0, 0.0, 0.0


def fitness_function(fz, fp1, fp2):
    height, width_ps, level1, level0 = simulate_eye(fz, fp1, fp2)

    swing = level1 - level0
    if swing <= 0:
        swing = 1e-6  # 防止除零

    # ✅ 三部分归一化得分
    norm_width = min(width_ps / MAX_EYE_WIDTH_PS, 1.0)
    norm_abs_height = min(height / MAX_ABS_EYE_HEIGHT_V, 1.0)
    norm_rel_height = min(height / swing, 1.0)

    score = (
            WIDTH_WEIGHT * norm_width +
            ABS_HEIGHT_WEIGHT * norm_abs_height +
            REL_HEIGHT_WEIGHT * norm_rel_height
    )
    score = max(0.0, min(score, 1.0))  # 确保在 [0, 1]

    return score, height, width_ps, level1, level0


def initialize_population():
    population = []
    for _ in range(POPULATION_SIZE):
        fz = random.uniform(*FZ_RANGE)
        fp1 = random.uniform(*FP1_RANGE)
        fp2 = random.uniform(*FP2_RANGE)
        population.append((fz, fp1, fp2))
    return population


def select(population):
    fitness_scores = [fitness_function(*ind)[0] for ind in population]
    total_score = sum(fitness_scores)
    if total_score == 0:
        return random.choices(population, k=POPULATION_SIZE)
    probabilities = [score / total_score for score in fitness_scores]
    selected = random.choices(population, weights=probabilities, k=POPULATION_SIZE)
    return selected


def crossover(parent1, parent2):
    if random.random() < CROSSOVER_RATE:
        cross_point = random.randint(0, 2)
        child1 = list(parent1)
        child2 = list(parent2)
        child1[cross_point:] = parent2[cross_point:]
        child2[cross_point:] = parent1[cross_point:]
        return tuple(child1), tuple(child2)
    else:
        return parent1, parent2


def mutate(individual):
    fz, fp1, fp2 = individual
    if random.random() < MUTATION_RATE:
        fz += random.uniform(-0.5, 0.5)
        fz = max(FZ_RANGE[0], min(FZ_RANGE[1], fz))
    if random.random() < MUTATION_RATE:
        fp1 += random.uniform(-1, 1)
        fp1 = max(FP1_RANGE[0], min(FP1_RANGE[1], fp1))
    if random.random() < MUTATION_RATE:
        fp2 += random.uniform(-2, 2)
        fp2 = max(FP2_RANGE[0], min(FP2_RANGE[1], fp2))
    return (fz, fp1, fp2)


# ===================== 热力图绘制 =====================
def plot_eye_heatmap(ax, df, title):
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
    im = ax.imshow(
        heatmap,
        extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
        origin='lower',
        aspect='auto',
        cmap='viridis',
        interpolation='bilinear'
    )
    ax.set_xlabel('时间 (ps)')
    ax.set_ylabel('电压 (V)')
    ax.set_title(title)
    ax.grid(False)


# ===================== 遗传算法主流程 =====================
def genetic_algorithm():
    population = initialize_population()
    best_individual = None
    best_score = 0
    best_height = 0
    best_width = 0
    best_level1 = 0
    best_level0 = 0

    target_output_dir = os.path.join(workspace_path, r"data/python_data")
    raw_csv_filename = os.path.join(target_output_dir, f"{target_probe}_眼图原始数据.csv")

    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.ion()
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.suptitle('遗传算法优化过程 - 实时眼图（热力图）')
    plt.show()

    ga_start_time = time.time()

    for gen in range(GENERATIONS):
        print(f"\n=== 第 {gen + 1} 代 ===")
        gen_scores = []

        for ind in population:
            score, height, width, level1, level0 = fitness_function(*ind)
            gen_scores.append((score, ind, height, width, level1, level0))
            if score > best_score:
                best_score = score
                best_individual = ind
                best_height = height
                best_width = width
                best_level1 = level1
                best_level0 = level0

        gen_scores.sort(reverse=True)
        top_score, top_ind, top_h, top_w, top_l1, top_l0 = gen_scores[0]
        fz, fp1, fp2 = top_ind

        swing = top_l1 - top_l0
        rel_ratio = top_h / swing if swing > 0 else 0

        print(f"当前最优：零点={fz:.2f}GHz, 极点1={fp1:.2f}GHz, 极点2={fp2:.2f}GHz")
        print(f"眼高={top_h:.4f}V, 眼宽={top_w:.2f}ps, 摆幅={swing:.4f}V")
        print(f"绝对眼高比例={top_h / MAX_ABS_EYE_HEIGHT_V:.3f}, 相对眼高比例={rel_ratio:.3f}")
        print(f"适应度得分={top_score:.4f}")

        # 再次仿真确保 CSV 最新
        simulate_eye(fz, fp1, fp2)

        try:
            df = pd.read_csv(raw_csv_filename, encoding="utf-8-sig")
            plot_eye_heatmap(
                ax=ax,
                df=df,
                title=f'第 {gen + 1} 代最优眼图\n零点={fz:.2f}GHz, 极点1={fp1:.2f}GHz, 极点2={fp2:.2f}GHz'
            )
            gen_img_path = os.path.join(target_output_dir, f"gen{gen + 1}_eye_heatmap.png")
            fig.savefig(gen_img_path, dpi=150, bbox_inches='tight')
            print(f"✅ 第 {gen + 1} 代热力图已保存至：{gen_img_path}")
            plt.pause(0.01)
        except Exception as e:
            print(f"⚠️ 绘图失败: {e}")

        # 👇 纯遗传操作（计入计时）
        selected = select(population)
        next_population = []
        for i in range(0, POPULATION_SIZE, 2):
            p1 = selected[i]
            p2 = selected[i + 1] if i + 1 < POPULATION_SIZE else selected[0]
            c1, c2 = crossover(p1, p2)
            next_population.extend([c1, c2])
        next_population = [mutate(ind) for ind in next_population[:POPULATION_SIZE]]
        population = next_population

    ga_end_time = time.time()
    pure_ga_time = ga_end_time - ga_start_time
    plt.ioff()
    return best_individual, best_score, best_height, best_width, best_level1, best_level0, pure_ga_time


# ===================== 主程序 =====================
if __name__ == "__main__":
    de.open_workspace(workspace_path)
    print("===== 开始遗传算法优化（3代） =====")

    result = genetic_algorithm()
    best_params, best_score, best_height, best_width, best_level1, best_level0, pure_ga_time = result
    best_fz, best_fp1, best_fp2 = best_params

    swing = best_level1 - best_level0
    abs_ratio = best_height / MAX_ABS_EYE_HEIGHT_V
    rel_ratio = best_height / swing if swing > 0 else 0

    print("\n===== 最优参数结果 =====")
    print(f"最优零点频率：{best_fz:.2f} GHz")
    print(f"最优极点1频率：{best_fp1:.2f} GHz")
    print(f"最优极点2频率：{best_fp2:.2f} GHz")
    print(f"眼高：{best_height:.4f} V")
    print(f"眼宽：{best_width:.2f} ps")
    print(f"Level1：{best_level1:.4f} V, Level0：{best_level0:.4f} V")
    print(f"信号摆幅：{swing:.4f} V")
    print(f"绝对眼高比例（/1.0V）：{abs_ratio:.3f}")
    print(f"相对眼高比例（/摆幅）：{rel_ratio:.3f}")
    print(f"适应度得分：{best_score:.4f}")

    # 最终仿真
    print("\n===== 生成最终最优眼图 =====")
    simulate_eye(best_fz, best_fp1, best_fp2)

    target_output_dir = os.path.join(workspace_path, r"data/python_data")
    raw_csv_filename = os.path.join(target_output_dir, f"{target_probe}_眼图原始数据.csv")
    df = pd.read_csv(raw_csv_filename, encoding="utf-8-sig")

    fig_final, ax_final = plt.subplots(figsize=(8, 6))
    plot_eye_heatmap(
        ax=ax_final,
        df=df,
        title=f'最终最优眼图\n零点={best_fz:.2f}GHz, 极点1={best_fp1:.2f}GHz, 极点2={best_fp2:.2f}GHz'
    )
    final_img_path = os.path.join(target_output_dir, "best_eye_diagram_heatmap.png")
    fig_final.savefig(final_img_path, dpi=300, bbox_inches='tight')
    plt.close(fig_final)
    print(f"✅ 最终热力图眼图已保存至：{final_img_path}")

    # 保存最优参数
    best_params_data = {
        "参数名称": [
            "零点频率(GHz)", "极点1频率(GHz)", "极点2频率(GHz)",
            "眼高(V)", "眼宽(ps)", "Level1(V)", "Level0(V)",
            "信号摆幅(V)", "绝对眼高比例(/1V)", "相对眼高比例(/摆幅)", "适应度得分"
        ],
        "数值": [
            best_fz, best_fp1, best_fp2,
            best_height, best_width, best_level1, best_level0,
            swing, abs_ratio, rel_ratio, best_score
        ]
    }
    df_best = pd.DataFrame(best_params_data)
    best_csv_path = os.path.join(target_output_dir, "最优零极点参数.csv")
    df_best.to_csv(best_csv_path, index=False, encoding="utf-8-sig")
    print(f"✅ 最优参数已保存至：{best_csv_path}")

    print(f"\n🔥 纯遗传算法操作耗时（不含仿真与绘图）：{pure_ga_time:.3f} 秒")