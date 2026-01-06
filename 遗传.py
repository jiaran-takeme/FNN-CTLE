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

# ===================== 全局配置 =====================
# 定义pi常量（替代math.pi）
pi = 3.141592653

# ADS路径配置
workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"
target_probe = "Eye_Probe1"
# 初始参数（mS/fF）
gm = 35
cp = 87
# 遗传算法配置
POPULATION_SIZE = 20  # 种群大小
GENERATIONS = 10  # 迭代代数
MUTATION_RATE = 0.1  # 变异概率
CROSSOVER_RATE = 0.8  # 交叉概率
# 零极点频率范围（GHz，角频率=2πf）
FZ_RANGE = (1, 12)  # 零点频率范围：1-12GHz
FP1_RANGE = (12, 24)  # 极点1频率范围：12-24GHz
FP2_RANGE = (24, 48)  # 极点2频率范围：24-48GHz
# 适应度权重（眼高/眼宽）
HEIGHT_WEIGHT = 0.6
WIDTH_WEIGHT = 0.4


# ===================== 核心函数 =====================
def UCIe(gm, cp, zero_list, poles_list):
    """计算增益参数（使用自定义pi），返回Apre的字符串形式"""
    # 解析表达式时使用全局定义的pi
    global pi
    wz_val = eval(zero_list[0])
    wp1_val = eval(poles_list[0])
    wp2_val = eval(poles_list[1])
    gm_S = gm * 1e-3
    cp_F = cp * 1e-15
    Aac = gm_S / (cp_F * wp2_val)
    Adc = (wz_val * Aac) / wp1_val
    Apre = (Adc * wp1_val * wp2_val) / wz_val

    # 将数值Apre转换为字符串（保留6位小数，适配ADS参数格式）
    Apre_str = f"{Apre:.6f}"

    # 可选：如果需要科学计数法格式（比如数值过大/过小），可改用下面这行
    # Apre_str = f"{Apre:.6e}"

    return Apre_str

def simulate_eye(fz, fp1, fp2, gm=gm, cp=cp):
    """
    执行ADS仿真，返回眼高、眼宽
    :param fz: 零点频率（GHz）
    :param fp1: 极点1频率（GHz）
    :param fp2: 极点2频率（GHz）
    :return: height(眼高/V), width_ps(眼宽/ps)
    """
    # 1. 构造零极点表达式（使用pi而非math.pi）
    zero = [f"(-{fz}e9)*(2*pi)"]
    poles = [f"(-{fp1}e9)*(2*pi)", f"(-{fp2}e9)*(2*pi)"]

    # 2. 计算Apre
    Apre = UCIe(gm, cp, zero, poles)

    # 3. 连接ADS并更新参数
    try:
        design = db.open_design(name=(library_name, cell_name, "schematic"))
        rx_diff1 = design.find_instance("Rx_Diff1")
        rx_diff1.parameters['Gain'].value = Apre
        rx_diff1.parameters['Zero'].value = zero
        rx_diff1.parameters['Pole'].value = poles
        rx_diff1.update_item_annotation()

        # 4. 生成网表并仿真
        netlist = design.generate_netlist()
        simulator = ads.CircuitSimulator()
        target_output_dir = os.path.join(workspace_path, r"data/python_data")
        simulator.run_netlist(netlist, output_dir=target_output_dir)

        # 5. 读取仿真结果
        output_data = dataset.open(Path(os.path.join(target_output_dir, f"{cell_name}.ds")))

        # 定位眼图测量块
        eye_meas_block = None
        for datablock in output_data.find_varblocks_with_var_name("Height"):
            if target_probe in datablock.name:
                eye_meas_block = datablock.name
                break
        if not eye_meas_block:
            raise ValueError("未找到眼图测量块")

        # 提取眼高、眼宽
        my_eye_meas = output_data[eye_meas_block].to_dataframe().reset_index()
        height = my_eye_meas["Height"].iloc[0]
        width_s = my_eye_meas["Width"].iloc[0]
        width_ps = width_s * 1e12

        return height, width_ps

    except Exception as e:
        print(f"仿真出错：{e}")
        return 0, 0  # 出错时返回最差值


def fitness_function(fz, fp1, fp2):
    """
    适应度函数：综合眼高和眼宽计算得分（越高越好）
    """
    height, width_ps = simulate_eye(fz, fp1, fp2)
    # 归一化（基于参数范围的经验最大值，可根据实际调整）
    norm_height = height / 1.0  # 假设眼高最大约1V
    norm_width = width_ps / 20  # 假设眼宽最大约20ps
    # 加权得分（防止负数）
    score = max(0, HEIGHT_WEIGHT * norm_height + WIDTH_WEIGHT * norm_width)
    return score, height, width_ps


def initialize_population():
    """初始化种群：每个个体是(fz, fp1, fp2)"""
    population = []
    for _ in range(POPULATION_SIZE):
        fz = random.uniform(*FZ_RANGE)
        fp1 = random.uniform(*FP1_RANGE)
        fp2 = random.uniform(*FP2_RANGE)
        population.append((fz, fp1, fp2))
    return population


def select(population):
    """选择操作：轮盘赌法"""
    # 计算每个个体的适应度得分
    fitness_scores = [fitness_function(*ind)[0] for ind in population]
    total_score = sum(fitness_scores)
    if total_score == 0:
        return random.choices(population, k=POPULATION_SIZE)  # 全0时随机选
    # 计算选择概率
    probabilities = [score / total_score for score in fitness_scores]
    # 选择下一代
    selected = random.choices(population, weights=probabilities, k=POPULATION_SIZE)
    return selected


def crossover(parent1, parent2):
    """交叉操作：单点交叉"""
    if random.random() < CROSSOVER_RATE:
        # 随机选择交叉点（0:fz,1:fp1,2:fp2）
        cross_point = random.randint(0, 2)
        child1 = list(parent1)
        child2 = list(parent2)
        child1[cross_point:] = parent2[cross_point:]
        child2[cross_point:] = parent1[cross_point:]
        return tuple(child1), tuple(child2)
    else:
        return parent1, parent2


def mutate(individual):
    """变异操作：随机微调参数"""
    fz, fp1, fp2 = individual
    # 零点变异
    if random.random() < MUTATION_RATE:
        fz += random.uniform(-0.5, 0.5)
        fz = max(FZ_RANGE[0], min(FZ_RANGE[1], fz))  # 限制范围
    # 极点1变异
    if random.random() < MUTATION_RATE:
        fp1 += random.uniform(-1, 1)
        fp1 = max(FP1_RANGE[0], min(FP1_RANGE[1], fp1))
    # 极点2变异
    if random.random() < MUTATION_RATE:
        fp2 += random.uniform(-2, 2)
        fp2 = max(FP2_RANGE[0], min(FP2_RANGE[1], fp2))
    return (fz, fp1, fp2)


def genetic_algorithm():
    """遗传算法主流程"""
    # 1. 初始化种群
    population = initialize_population()
    best_individual = None
    best_score = 0
    best_height = 0
    best_width = 0

    # 2. 迭代优化
    for gen in range(GENERATIONS):
        print(f"\n=== 第 {gen + 1} 代 ===")
        # 计算适应度并记录最优
        gen_scores = []
        for ind in population:
            score, height, width = fitness_function(*ind)
            gen_scores.append((score, ind, height, width))
            # 更新全局最优
            if score > best_score:
                best_score = score
                best_individual = ind
                best_height = height
                best_width = width

        # 打印当前代信息
        gen_scores.sort(reverse=True)
        top_score, top_ind, top_h, top_w = gen_scores[0]
        print(f"当前最优：零点={top_ind[0]:.2f}GHz, 极点1={top_ind[1]:.2f}GHz, 极点2={top_ind[2]:.2f}GHz")
        print(f"眼高={top_h:.4f}V, 眼宽={top_w:.2f}ps, 适应度得分={top_score:.4f}")

        # 3. 选择
        selected = select(population)
        # 4. 交叉
        next_population = []
        for i in range(0, POPULATION_SIZE, 2):
            p1 = selected[i]
            p2 = selected[i + 1] if i + 1 < POPULATION_SIZE else selected[0]
            c1, c2 = crossover(p1, p2)
            next_population.append(c1)
            next_population.append(c2)
        # 5. 变异
        next_population = [mutate(ind) for ind in next_population[:POPULATION_SIZE]]
        # 更新种群
        population = next_population

    # 3. 返回最优结果
    return best_individual, best_score, best_height, best_width


# ===================== 执行流程 =====================
if __name__ == "__main__":
    # 1. 打开ADS工作区
    de.open_workspace(workspace_path)

    # 2. 运行遗传算法优化
    print("===== 开始遗传算法优化 =====")
    best_params, best_score, best_height, best_width = genetic_algorithm()
    best_fz, best_fp1, best_fp2 = best_params

    # 3. 打印最优结果
    print("\n===== 最优参数结果 =====")
    print(f"最优零点频率：{best_fz:.2f} GHz")
    print(f"最优极点1频率：{best_fp1:.2f} GHz")
    print(f"最优极点2频率：{best_fp2:.2f} GHz")
    print(f"对应眼高：{best_height:.4f} V")
    print(f"对应眼宽：{best_width:.2f} ps")
    print(f"适应度得分：{best_score:.4f}")

    # 4. 用最优参数重新仿真并生成眼图
    print("\n===== 用最优参数生成眼图 =====")
    # 重新仿真
    height, width_ps = simulate_eye(best_fz, best_fp1, best_fp2)
    # 读取原始数据
    target_output_dir = os.path.join(workspace_path, r"data/python_data")
    raw_csv_filename = os.path.join(target_output_dir, f"{target_probe}_眼图原始数据.csv")
    df = pd.read_csv(raw_csv_filename, encoding="utf-8-sig")

    # 绘制眼图
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(8, 6))
    plt.scatter(df["时间(ps)"].values, df["密度值"].values, s=1, alpha=0.5, color='blue')
    plt.xlabel('时间 (ps)')
    plt.ylabel('电压 (V)')
    plt.title(f'最优参数眼图（零点={best_fz:.2f}GHz，极点1={best_fp1:.2f}GHz，极点2={best_fp2:.2f}GHz）')
    plt.grid(True, alpha=0.3)

    # 保存眼图
    save_path = os.path.join(target_output_dir, r"best_eye_diagram.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.show()
    print(f"✅ 最优参数眼图已保存到：{save_path}")

    # 5. 保存最优参数到CSV
    best_params_data = {
        "参数名称": ["零点频率(GHz)", "极点1频率(GHz)", "极点2频率(GHz)", "眼高(V)", "眼宽(ps)", "适应度得分"],
        "数值": [best_fz, best_fp1, best_fp2, best_height, best_width, best_score]
    }
    df_best = pd.DataFrame(best_params_data)
    best_csv_filename = os.path.join(target_output_dir, "最优零极点参数.csv")
    df_best.to_csv(best_csv_filename, index=False, encoding="utf-8-sig")
    print(f"✅ 最优参数已保存到：{best_csv_filename}")