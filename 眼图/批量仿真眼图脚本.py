# -*- coding: utf-8 -*-
"""
批量生成眼图原始数据
零极点 + Apre 全部随机范围
每次自动保存独立的眼图原始数据 CSV
文件名包含所有参数：序号_零点_极点1_极点2_增益
"""

import warnings
import random
import os
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

# Keysight ADS 相关
from keysight.ads import de
from keysight.ads.de import db_uu as db
from keysight.edatoolbox import ads
import keysight.ads.dataset as dataset

# ===================== 全局配置 =====================
workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"
target_probe = "Eye_Probe1"
target_output_dir = os.path.join(workspace_path, r"data/python_data")
os.makedirs(target_output_dir, exist_ok=True)

# ===================== 仿真函数 =====================
def run_ads_simulation(zero_ghz, pole1_ghz, pole2_ghz, Apre_val, save_index):
    zero = [f"(-{zero_ghz}e9)*(2*pi)"]
    poles = [f"(-{pole1_ghz}e9)*(2*pi)", f"(-{pole2_ghz}e9)*(2*pi)"]
    Apre = str(Apre_val)

    # --- 执行仿真 ---
    try:
        design = db.open_design(name=(library_name, cell_name, "schematic"))
        rx_diff1 = design.find_instance("Rx_Diff1")

        rx_diff1.parameters['Gain'].value = Apre
        rx_diff1.parameters['Zero'].value = zero
        rx_diff1.parameters['Pole'].value = poles
        rx_diff1.update_item_annotation()

        netlist = design.generate_netlist()
        simulator = ads.CircuitSimulator()
        os.makedirs(target_output_dir, exist_ok=True)
        simulator.run_netlist(netlist, output_dir=target_output_dir)
    except Exception as e:
        print(f"❌ 仿真执行失败: {e}")
        return 0.0, 0.0

    try:
        ds_path = Path(target_output_dir) / f"{cell_name}.ds"
        output_data = dataset.open(ds_path)

        # 读取眼高、眼宽
        eye_meas_block = None
        for b in output_data.find_varblocks_with_var_name("Height"):
            if target_probe in b.name:
                eye_meas_block = b.name
                break
        if not eye_meas_block:
            raise ValueError("未找到眼图测量块")

        df_meas = output_data[eye_meas_block].to_dataframe().reset_index()
        height = df_meas["Height"].iloc[0]
        width_ps = df_meas["Width"].iloc[0] * 1e12

        # 读取眼图原始数据
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

        # 🔥 保存：文件名包含所有仿真参数
        # 格式：Eye_序号_零点GHz_极点1GHz_极点2GHz_Apre值.csv
        filename = (f"Eye_{save_index:03d}_Z{zero_ghz:.2f}_P1{pole1_ghz:.2f}_P2{pole2_ghz:.2f}_A{Apre_val:.2e}.csv")
        raw_csv_filename = os.path.join(target_output_dir, filename)
        df_raw.to_csv(raw_csv_filename, index=False, encoding="utf-8-sig")
        print(f"✅ 眼图原始数据已保存: {filename}")

        return height, width_ps

    except Exception as e:
        print(f"❌ 读取数据失败: {e}")
        return 0.0, 0.0

# ===================== 打开工作空间（只打开一次） =====================
de.open_workspace(workspace_path)

# ===================== 批量循环 =====================
total_cycles = 50  # 想跑多少次改这里

for idx in range(1, total_cycles + 1):
    print(f"\n==================== 第 {idx}/{total_cycles} 次仿真 ====================")

    # 随机参数范围（原版不变）
    fz = random.uniform(1, 12)
    fp1 = random.uniform(12, 24)
    fp2 = random.uniform(24, 48)
    Apre_val = random.uniform(10e10, 50e10)

    print(f"参数 → zero={fz:.2f}GHz | pole1={fp1:.2f}GHz | pole2={fp2:.2f}GHz | Apre={Apre_val:.2e}")

    # 运行仿真
    height, width_ps = run_ads_simulation(fz, fp1, fp2, Apre_val, idx)
    print(f"✅ 仿真完成 → 眼高：{height:.4f} V | 眼宽：{width_ps:.2f} ps")

print("\n🎉 全部批量仿真完成！")