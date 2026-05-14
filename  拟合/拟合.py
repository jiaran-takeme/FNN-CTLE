import numpy as np
import pandas as pd

# ----------------------------
# 1. 模型参数（输入单位：GHz）
# ----------------------------
f_zero_GHz = -4.44
f_pole1_GHz = -18.69
f_pole2_GHz = -26.0
A_pre = 402298850574.7126

# 转换为 s 域（rad/s）
z1 = 2 * np.pi * f_zero_GHz * 1e9
p1 = 2 * np.pi * f_pole1_GHz * 1e9
p2 = 2 * np.pi * f_pole2_GHz * 1e9

# ----------------------------
# 2. 构建模型参数表
# ----------------------------
param_df = pd.DataFrame({
    'Element': ['Zero', 'Pole 1', 'Pole 2', 'A_pre'],
    'Real_Part (rad/s)': [z1, p1, p2, A_pre],
    'Imaginary_Part (rad/s)': [0.0, 0.0, 0.0, 0.0]
})

# ----------------------------
# 3. 生成频率响应（0.1 GHz 步长）
# ----------------------------
f_start_GHz = 0.1
f_stop_GHz = 100.0
f_step_GHz = 0.1

freq_GHz = np.arange(f_start_GHz, f_stop_GHz + f_step_GHz, f_step_GHz)
freq_Hz = freq_GHz * 1e9
s = 1j * 2 * np.pi * freq_Hz

# 计算 H(s)
H_s = A_pre * (s - z1) / ((s - p1) * (s - p2))

# 构建响应数据表
response_df = pd.DataFrame({
    'Frequency (GHz)': freq_GHz,
    'Real Part': H_s.real,
    'Imaginary Part': H_s.imag
})

# ----------------------------
# 4. 保存到 Excel（两个 sheet）
# ----------------------------
output_file = "Hs_transfer_function_response.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    param_df.to_excel(writer, sheet_name='Model Parameters', index=False)
    response_df.to_excel(writer, sheet_name='Frequency Response', index=False)

print(f"✅ 数据已成功保存到 '{output_file}'")
print("  - Sheet 'Model Parameters': 零点、极点、增益")
print("  - Sheet 'Frequency Response': 频率(GHz)、实部、虚部（步长 0.1 GHz）")