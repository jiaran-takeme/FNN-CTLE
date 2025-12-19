from keysight.ads import de
from keysight.ads.de import db_uu as db
import os
from keysight.edatoolbox import ads
import keysight.ads.dataset as dataset
import matplotlib.pyplot as plt
from IPython.core import getipython
from pathlib import Path
import numpy as np

workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"
target_probe = "Eye_Probe1"
# 打开工作空间
de.open_workspace(workspace_path)
design = db.open_design(name=(library_name, cell_name, "schematic"))
# 修改参数
try:
    pass
except:
    pass
# 生成网表
netlist = design.generate_netlist()
print(netlist)
simulator = ads.CircuitSimulator()
target_output_dir = os.path.join(workspace_path, "data")
simulator.run_netlist(netlist, output_dir=target_output_dir)
# 仿真结果
output_data = dataset.open(
    Path(os.path.join(target_output_dir, f"{cell_name}" + ".ds"))
)

# 定位测量块（Height/Width）
TARGET_PROBE = "EyeDiff_Probe1"
eye_meas_block = None
for datablock in output_data.find_varblocks_with_var_name("Height"):
    if target_probe in datablock.name:
        eye_meas_block = datablock.name
        break

# 定位原始块（time/Density）
eye_raw_block = None
for datablock in output_data.find_varblocks_with_var_name("Density"):
    if target_probe in datablock.name:
        eye_raw_block = datablock.name
        break

my_eye_meas = output_data[eye_meas_block].to_dataframe().reset_index()
