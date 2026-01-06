# main.py
import os
import matplotlib.pyplot as plt
import pandas as pd
from simulator import ADSSimulator
from genetic_optimizer import GeneticOptimizer

# ===================== 全局配置 =====================
workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
library_name = "FNN_CTLE_lib"
cell_name = "cell_testbench"
target_probe = "Eye_Probe1"

# 遗传算法参数
POPULATION_SIZE = 20
GENERATIONS = 10
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8
FZ_RANGE = (1, 12)
FP1_RANGE = (12, 24)
FP2_RANGE = (24, 48)
HEIGHT_WEIGHT = 0.6
WIDTH_WEIGHT = 0.4

if __name__ == "__main__":
    from keysight.ads import de
    de.open_workspace(workspace_path)

    # 初始化仿真器
    simulator = ADSSimulator(
        workspace_path=workspace_path,
        library_name=library_name,
        cell_name=cell_name,
        target_probe=target_probe,
        gm=35,
        cp=87
    )

    # 初始化并运行遗传算法
    optimizer = GeneticOptimizer(
        simulator=simulator,
        fz_range=FZ_RANGE,
        fp1_range=FP1_RANGE,
        fp2_range=FP2_RANGE,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS,
        mutation_rate=MUTATION_RATE,
        crossover_rate=CROSSOVER_RATE,
        height_weight=HEIGHT_WEIGHT,
        width_weight=WIDTH_WEIGHT
    )

    print("===== 开始遗传算法优化 =====")
    best_params, best_score, best_height, best_width = optimizer.optimize()
    best_fz, best_fp1, best_fp2 = best_params

    print("\n===== 最优参数结果 =====")
    print(f"最优零点频率：{best_fz:.2f} GHz")
    print(f"最优极点1频率：{best_fp1:.2f} GHz")
    print(f"最优极点2频率：{best_fp2:.2f} GHz")
    print(f"对应眼高：{best_height:.4f} V")
    print(f"对应眼宽：{best_width:.2f} ps")
    print(f"适应度得分：{best_score:.4f}")

    # 重新仿真获取眼图数据
    simulator.simulate_eye(best_fz, best_fp1, best_fp2)

    # 绘制眼图
    raw_csv = simulator.get_raw_eye_data_path()
    df = pd.read_csv(raw_csv, encoding="utf-8-sig")

    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(8, 6))
    plt.scatter(df["时间(ps)"], df["密度值"], s=1, alpha=0.5, color='blue')
    plt.xlabel('时间 (ps)')
    plt.ylabel('电压 (V)')
    plt.title(f'最优参数眼图（零点={best_fz:.2f}GHz，极点1={best_fp1:.2f}GHz，极点2={best_fp2:.2f}GHz）')
    plt.grid(True, alpha=0.3)

    target_output_dir = os.path.join(workspace_path, r"data/python_data")
    save_path = os.path.join(target_output_dir, "best_eye_diagram.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.show()
    print(f"✅ 最优参数眼图已保存到：{save_path}")

    # 保存最优参数
    best_params_data = {
        "参数名称": ["零点频率(GHz)", "极点1频率(GHz)", "极点2频率(GHz)", "眼高(V)", "眼宽(ps)", "适应度得分"],
        "数值": [best_fz, best_fp1, best_fp2, best_height, best_width, best_score]
    }
    df_best = pd.DataFrame(best_params_data)
    best_csv_filename = os.path.join(target_output_dir, "最优零极点参数.csv")
    df_best.to_csv(best_csv_filename, index=False, encoding="utf-8-sig")
    print(f"✅ 最优参数已保存到：{best_csv_filename}")