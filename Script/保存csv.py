import keysight.ads.dataset as dataset
import os
import numpy as np
import pandas as pd
from pathlib import Path

# ========== 1. 基础配置（仅改这3行） ==========
WORKSPACE_PATH = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
CELL_NAME = "cell_testbench"
TARGET_PROBE = "EyeDiff_Probe1"

# ========== 2. 打开数据集 + 定位目标块 ==========
target_output_dir = os.path.join(WORKSPACE_PATH, "data")
ds_file = Path(os.path.join(target_output_dir, f"{CELL_NAME}.ds"))
output_data = dataset.open(ds_file)

# 定位测量块（Height/Width）
eye_meas_block = None
for datablock in output_data.find_varblocks_with_var_name("Height"):
    if TARGET_PROBE in datablock.name:
        eye_meas_block = datablock.name
        break

# 定位原始块（time/Density）
eye_raw_block = None
for datablock in output_data.find_varblocks_with_var_name("Density"):
    if TARGET_PROBE in datablock.name:
        eye_raw_block = datablock.name
        break

# ========== 3. 提取所有数据（严格按你的列名） ==========
# 3.1 提取测量指标（眼高/眼宽等）
my_eye_meas = output_data[eye_meas_block].to_dataframe().reset_index()
# 整理测量指标（新增单位列，更易读）
meas_data = {
    "指标名称": ["眼高(V)", "眼宽(s)", "眼宽(ps)", "电平1(V)", "电平0(V)", "眼幅(V)"],
    "数值": [
        my_eye_meas["Height"].iloc[0],
        my_eye_meas["Width"].iloc[0],
        my_eye_meas["Width"].iloc[0] * 1e12,
        my_eye_meas["Level1"].iloc[0],
        my_eye_meas["Level0"].iloc[0],
        my_eye_meas["Level1"].iloc[0] - my_eye_meas["Level0"].iloc[0]
    ]
}
df_meas = pd.DataFrame(meas_data)

# 3.2 提取原始数据（time/Density）
my_eye_raw = output_data[eye_raw_block].to_dataframe().reset_index()
# 整理原始数据（新增time_ps列，转皮秒）
df_raw = pd.DataFrame({
    "索引": my_eye_raw["index"],
    "时间(s)": my_eye_raw["time"],
    "时间(ps)": my_eye_raw["time"] * 1e12,
    "密度值": my_eye_raw["Density"]
})

# ========== 4. 导出CSV（无任何第三方依赖，Excel可直接打开） ==========
# 4.1 导出测量指标CSV
meas_csv_filename = os.path.join(target_output_dir, f"{CELL_NAME}_{TARGET_PROBE}_眼图测量指标.csv")
df_meas.to_csv(meas_csv_filename, index=False, encoding="utf-8-sig")  # utf-8-sig确保Excel中文正常

# 4.2 导出原始数据CSV
raw_csv_filename = os.path.join(target_output_dir, f"{CELL_NAME}_{TARGET_PROBE}_眼图原始数据.csv")
df_raw.to_csv(raw_csv_filename, index=False, encoding="utf-8-sig")

# ========== 5. 打印导出结果（验证） ==========
print(f"✅ 测量指标CSV已保存到：{meas_csv_filename}")
print(f"✅ 原始数据CSV已保存到：{raw_csv_filename}")
print("\n=== 【眼图测量指标】预览 ===")
print(df_meas)
print("\n=== 【眼图原始数据】前10行预览 ===")
print(df_raw.head(10))