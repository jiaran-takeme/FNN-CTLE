import warnings
# 屏蔽所有类型的警告（最彻底）
warnings.filterwarnings("ignore")
from keysight.ads import de
from keysight.ads.de import db_uu as db
import os
from keysight.edatoolbox import ads
import keysight.ads.dataset as dataset
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import math

workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"
target_probe = "Eye_Probe1"
pi = 3.141592653
# 定义新格式的输入参数
gm = 35  # mS (毫西门子)
cp = 87  # fF (飞法)
zero = ['(-2e9)*(2*pi)']  # 修正为math.pi，保证解析正常
poles = ['(-16e9)*(2*pi)', '(-48e9)*(2*pi)']

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

Apre = UCIe(gm=gm, cp=cp, zero_list=zero, poles_list=poles)
print(f"Apre: {Apre}")

de.open_workspace(workspace_path)
design = db.open_design(name=(library_name, cell_name, "schematic"))

rx_diff1 = design.find_instance("Rx_Diff1")
rx_diff1.parameters['Gain'].value = Apre
rx_diff1.parameters['Zero'].value = zero
rx_diff1.parameters['Pole'].value = poles
rx_diff1.update_item_annotation()

# 生成网表
netlist = design.generate_netlist()
print(netlist)
simulator = ads.CircuitSimulator()
target_output_dir = os.path.join(workspace_path, r"data/python_data")
simulator.run_netlist(netlist, output_dir=target_output_dir)
# 仿真结果
output_data = dataset.open(
    Path(os.path.join(target_output_dir, f"{cell_name}" + ".ds"))
)

# 定位测量块（Height/Width）
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
my_eye_raw = output_data[eye_raw_block].to_dataframe().reset_index()

height = my_eye_meas["Height"].iloc[0]
width_s = my_eye_meas["Width"].iloc[0]
level1 = my_eye_meas["Level1"].iloc[0]
level0 = my_eye_meas["Level0"].iloc[0]

width_ps = width_s * 1e12
amplitude = level1 - level0

# 构建测量指标DataFrame
meas_data = {
    "指标名称": ["眼高(V)", "眼宽(s)", "眼宽(ps)", "电平1(V)", "电平0(V)", "眼幅(V)"],
    "数值": [height, width_s, width_ps, level1, level0, amplitude]
}
df_meas = pd.DataFrame(meas_data)

# 导出测量指标CSV
meas_csv_filename = os.path.join(target_output_dir, f"{cell_name}_{target_probe}_眼图测量指标.csv")
df_meas.to_csv(meas_csv_filename, index=False, encoding="utf-8-sig")

# 无需单独提取eye_time/eye_density等中间变量，直接在DataFrame中计算
df_raw = pd.DataFrame({
    "索引": my_eye_raw["index"],
    "时间(s)": my_eye_raw["time"],
    "时间(ps)": my_eye_raw["time"] * 1e12,
    "密度值": my_eye_raw["Density"]
})

# 导出原始数据CSV
raw_csv_filename = os.path.join(target_output_dir, f"{target_probe}_眼图原始数据.csv")
df_raw.to_csv(raw_csv_filename, index=False, encoding="utf-8-sig")

# ========== 3. 打印结果（精简：用已计算的变量，避免重复取值） ==========
print("\n=== 提取的核心指标 ===")
print(f"眼高：{height:.4f} V")
print(f"眼宽：{width_ps:.2f} ps")
print(f"眼幅：{amplitude:.4f} V")
print("\n=== Rx参数 ===")
print(f"增益：{Apre}")
print(f"零点：{zero}")
print(f"极点：{poles}")
# print(f"\n时间轴（前5个值，ps）：{df_raw['时间(ps)'].head().values}")
# print(f"密度（前5个值）：{df_raw['密度值'].head().values}")

## 眼图
csv_path = raw_csv_filename
df = pd.read_csv(csv_path, encoding="utf-8-sig")

# 2. 提取核心数据（时间+电压，这里“密度值”实际是电压值）
time_ps = df["时间(ps)"].values
voltage = df["密度值"].values  # 直接用这个作为电压

# 3. 绘制最简单的眼图（时间-电压散点图）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.figure(figsize=(8, 6))

# 核心：绘制时间-电压的散点（点大小调小，避免重叠）
plt.scatter(time_ps, voltage, s=1, alpha=0.5, color='blue')

# 4. 添加基础标注
plt.xlabel('时间 (ps)')
plt.ylabel('电压 (V)')
plt.title('EyeDiff_Probe')
plt.grid(True, alpha=0.3)

# 5. 保存+显示
save_path = os.path.join(target_output_dir, r"eye_diagram.png")
plt.tight_layout()
plt.savefig(save_path, dpi=300)
plt.show()

print(f"✅ 最简单眼图已保存到：{save_path}")