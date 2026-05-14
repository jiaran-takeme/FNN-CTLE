import numpy as np
import matplotlib.pyplot as plt

# IEEE 工程图标准：Arial
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 10,
    "axes.linewidth": 0.7,
    "axes.unicode_minus": True,
    "grid.linestyle": ":",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.3,
    "legend.frameon": False
})

# 约束函数 f(x)，单位 GHz
def constraint_fun(wz_ghz, wp1_ghz, Adc_dB):
    Adc = 10 ** (Adc_dB / 20)
    factor = np.sqrt((1 - np.sqrt(1 - Adc**2)) / 2)
    return wz_ghz - wp1_ghz * factor

# 50 组数据，横轴 0~50
N = 50
x = np.linspace(0, 50, N)

# 无约束
wp1_u = np.random.uniform(12, 24, N)
Adc_u = np.random.uniform(-6, 0, N)
Adc_lin = 10 ** (Adc_u / 20)
wz_theory = wp1_u * np.sqrt((1 - np.sqrt(1 - Adc_lin**2)) / 2)
wz_u = wz_theory + np.random.uniform(-0.6, 0.6, N)
f_unconstrained = constraint_fun(wz_u, wp1_u, Adc_u)

# 有约束
wp1_c = np.random.uniform(12, 24, N)
Adc_c = np.random.uniform(-6, 0, N)
Adc_lin_c = 10 ** (Adc_c / 20)
wz_c = wp1_c * np.sqrt((1 - np.sqrt(1 - Adc_lin_c**2)) / 2)
f_constrained = constraint_fun(wz_c, wp1_c, Adc_c)

# 绘图
fig, ax = plt.subplots(figsize=(7, 3.2))

ax.plot(x, f_unconstrained, 'r--', linewidth=0.9, label='Unconstrained')
ax.plot(x, f_constrained, 'b-', linewidth=1.4, label='With constraint')
ax.axhline(0, color='k', linewidth=0.7)

ax.set_xlabel('Sample Index')
ax.set_ylabel('Constraint residual $f(x)$ ')
ax.set_title('CTLE Zero-Pole Physical Constraint')
ax.set_xlim(0, 50)
ax.set_ylim(-1.0, 1.0)
ax.legend(loc='upper right')
ax.grid(True)

plt.tight_layout()
plt.show()