import pandas as pd
import matplotlib.pyplot as plt

# 1. 读取原始数据（你的CSV路径）
csv_path = r"C:\Users\zhaohongrui\Desktop\ADS\FNN_CTLE_wrk\data\cell_testbench_EyeDiff_Probe1_眼图原始数据.csv"
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
plt.title('最简单眼图 - EyeDiff_Probe1')
plt.grid(True, alpha=0.3)

# 5. 保存+显示
save_path = r"C:\Users\zhaohongrui\Desktop\ADS\FNN_CTLE_wrk\data\simple_eye_diagram.png"
plt.tight_layout()
plt.savefig(save_path, dpi=300)
plt.show()

print(f"✅ 最简单眼图已保存到：{save_path}")