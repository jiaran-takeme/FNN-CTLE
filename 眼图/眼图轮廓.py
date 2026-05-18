import pandas as pd
import matplotlib.pyplot as plt

# ===================== 读取眼图数据 =====================
df = pd.read_csv("Eye_Probe1_眼图原始数据.csv")

# ===================== 绘图设置 =====================
plt.figure(figsize=(10, 6))
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ===================== 绘制真实眼图（超多轨迹叠加） =====================
# 把每一条比特波形都画出来，叠在一起 = 真实眼图
for index_bit in df["索引"].unique():
    bit_data = df[df["索引"] == index_bit]
    plt.plot(
        bit_data["时间(ps)"],
        bit_data["电压(V)"],
        color="blue",        # 眼图颜色
        alpha=0.1,          # 透明度（叠多了就像眼图）
        linewidth=0.3
    )

# ===================== 样式 =====================
plt.xlabel("时间 (ps)")
plt.ylabel("电压 (V)")
plt.title("真实眼图波形", fontsize=14)
plt.grid(False)
plt.xlim(df["时间(ps)"].min(), df["时间(ps)"].max())
plt.ylim(-0.1, 0.1)
plt.tight_layout()
plt.show()