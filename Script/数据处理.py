import keysight.ads.dataset as dataset
import os
import numpy as np
import pandas as pd
from pathlib import Path

# ========== 1. 基础配置（和教程一致） ==========
WORKSPACE_PATH = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
CELL_NAME = "cell_testbench"
target_output_dir = os.path.join(WORKSPACE_PATH, "data")
ds_file = Path(os.path.join(target_output_dir, f"{CELL_NAME}.ds"))

# 2. 打开数据集（教程第一步）
output_data = dataset.open(ds_file)

# 3. 定位目标块（教程逻辑：先找变量名→筛选探针）
# 3.1 定位眼图测量块（对应教程SP1.SP）
eye_meas_block = None
for datablock in output_data.find_varblocks_with_var_name("Height"):
    if "EyeDiff_Probe1" in datablock.name:
        eye_meas_block = datablock.name
        break

# 3.2 定位眼图原始块（对应教程groupdelay块）
eye_raw_block = None
for datablock in output_data.find_varblocks_with_var_name("Density"):
    if "EyeDiff_Probe1" in datablock.name:
        eye_raw_block = datablock.name
        break

# ========== 4. 严格复刻教程：先转DataFrame→再看列名→最后提取（核心！） ==========
# 4.1 测量块转DataFrame（教程：mydata = output_data[sp].to_dataframe().reset_index()）
my_eye_meas = output_data[eye_meas_block].to_dataframe().reset_index()
print("=== 【教程第一步】测量块DataFrame列名（先看列名再提取）===")
print(my_eye_meas.columns.tolist())  # 教程不会跳过这步，先确认列名
print("测量块DataFrame内容：\n", my_eye_meas)

# 4.2 原始块转DataFrame（教程：mygd = output_data[gd].to_dataframe().reset_index()）
my_eye_raw = output_data[eye_raw_block].to_dataframe().reset_index()
print("\n=== 【教程第一步】原始块DataFrame列名（先看列名再提取）===")
print(my_eye_raw.columns.tolist())  # 关键！你的列名是['index', 'time', 'Density']
print("原始块DataFrame前5行：\n", my_eye_raw.head())

# ========== 5. 严格按教程：按真实列名提取（绝不编列名） ==========
# 5.1 提取测量指标（教程：freq = mydata["freq"] / 1e6）
# 你的列名：['index', 'Level1', 'Height', 'Level0', 'Width'] → 直接用
eye_height = my_eye_meas["Height"].iloc[0]    # 教程逻辑：按列名提取
eye_width = my_eye_meas["Width"].iloc[0]      # 教程逻辑：按列名提取
level1 = my_eye_meas["Level1"].iloc[0]        # 教程逻辑：按列名提取
level0 = my_eye_meas["Level0"].iloc[0]        # 教程逻辑：按列名提取

# 教程逻辑：单位转换（freq / 1e6 → eye_width * 1e12）
eye_width_ps = eye_width * 1e12
eye_amplitude = level1 - level0  # 教程逻辑：数据转换（S21 = 20*log10(abs(...))）

# 5.2 提取原始数据（教程：提取freq/S21 → 提取time/Density）
# 你的列名：['index', 'time', 'Density'] → 只用这三个列名
eye_time = my_eye_raw["time"].values          # 严格按你的列名（小写time）
eye_density = my_eye_raw["Density"].values    # 严格按你的列名
eye_time_ps = eye_time * 1e12                 # 教程逻辑：单位转换

# ========== 6. 打印结果（教程逻辑：打印freq/S21/S11） ==========
print("\n=== 【教程最终结果】提取的核心指标 ===")
print(f"眼高（对应教程S21）：{eye_height:.4f} V")
print(f"眼宽（原始，对应教程freq）：{eye_width:.8f} s")
print(f"眼宽（转ps，对应教程freq/1e6）：{eye_width_ps:.2f} ps")
print(f"眼幅（对应教程S11）：{eye_amplitude:.4f} V")
print(f"\n时间轴（前5个值，转ps，对应教程freq）：{eye_time_ps[:5]}")
print(f"密度（前5个值，对应教程GroupDelay）：{eye_density[:5]}")