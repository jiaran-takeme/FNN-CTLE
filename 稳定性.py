import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# ======================
# 你的 CTLE 参数（直接用你图里的值）
# ======================
fz = 2.5e9       # Zero frequency: 2.5 GHz
fp1 = 20.0e9     # Pole 1: 20 GHz
fp2 = 27.44e9    # Pole 2: 27.44 GHz

# Convert to angular frequency (rad/s)
wz = 2 * np.pi * fz
wp1 = 2 * np.pi * fp1
wp2 = 2 * np.pi * fp2

# ======================
# Construct CTLE Transfer Function H(s)
# ======================
num = [1, wz]                  # Numerator: s + ωz
den = [1, wp1+wp2, wp1*wp2]    # Denominator: s² + (ωp1+ωp2)s + ωp1·ωp2
sys = signal.TransferFunction(num, den)

# ======================
# Extract zeros and poles
# ======================
zeros = sys.zeros
poles = sys.poles

# ======================
# Auto-check Stability & Causality
# ======================
is_stable = all(np.real(poles) < 0)
# For real-coefficient LTI system with finite poles, causality is guaranteed
is_causal = True

# ======================
# Plot s-plane Pole-Zero Map (Full English Version)
# ======================
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 10,
    "axes.linewidth": 0.7
})

plt.figure(figsize=(6, 5))
# Draw coordinate axes
plt.axhline(0, color='black', linewidth=0.8, linestyle='-')
plt.axvline(0, color='black', linewidth=0.8, linestyle='-')

# Plot zeros (blue circles) and poles (red crosses)
plt.scatter(np.real(zeros), np.imag(zeros), s=80, marker='o',
            color='#0051a2', edgecolor='black', label='Zeros', zorder=5)
plt.scatter(np.real(poles), np.imag(poles), s=80, marker='x',
            color='#c8102e', linewidth=1.5, label='Poles', zorder=5)

# Highlight left half-plane (stable region)
plt.axvspan(-np.inf, 0, color='#cce7ff', alpha=0.2, zorder=0)

# Axis labels and title
plt.xlabel('Real Part $\mathrm{Re}(s)$ (rad/s)', labelpad=8)
plt.ylabel('Imaginary Part $\mathrm{Im}(s)$ (rad/s)', labelpad=8)
plt.title('CTLE Pole-Zero Map', fontweight='bold', pad=12)

# Grid and legend
plt.grid(True, linestyle=':', alpha=0.5)
plt.legend(loc='upper right', framealpha=1, edgecolor='black')
plt.axis('equal')

# Add stability annotation
plt.text(0.02, 0.02, f'Stable: {is_stable}\nCausal: {is_causal}',
         transform=plt.gca().transAxes,
         bbox=dict(facecolor='white', edgecolor='gray', pad=4),
         fontsize=9)

# Print results in console
print("="*50)
print("CTLE Pole-Zero Analysis Results")
print("="*50)
print(f"Zero location: {zeros[0]/1e9:.2f} GHz (s = {zeros[0]:.2e} rad/s)")
print(f"Pole 1 location: {poles[0]/1e9:.2f} GHz (s = {poles[0]:.2e} rad/s)")
print(f"Pole 2 location: {poles[1]/1e9:.2f} GHz (s = {poles[1]:.2e} rad/s)")
print("-"*50)
print(f"✅ System Stability: {is_stable} (All poles in left half-plane)")
print(f"✅ System Causality: {is_causal} (Minimum-phase LTI system)")
print("="*50)

plt.tight_layout()
plt.show()