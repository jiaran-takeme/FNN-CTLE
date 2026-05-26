import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def extract_diamond_mask_tight(csv_path, center_t=21.5, center_v=0.0):
    df = pd.read_csv(csv_path)
    t = df["时间(ps)"].values
    v = df["电压(V)"].values

    # 二维直方图：统计每个格子有没有点
    bins_t = 200
    bins_v = 100
    counts, t_edges, v_edges = np.histogram2d(t, v, bins=[bins_t, bins_v])
    counts = counts.T  # (v_bins, t_bins)

    # 中心格子索引
    center_t_idx = np.argmin(np.abs((t_edges[:-1] + t_edges[1:])/2 - center_t))
    center_v_idx = np.argmin(np.abs((v_edges[:-1] + v_edges[1:])/2 - center_v))

    # 上顶点：从中心向上找第一个非零
    top_idx = center_v_idx
    while top_idx < counts.shape[0] - 1 and counts[top_idx, center_t_idx] == 0:
        top_idx += 1
    top_v = (v_edges[top_idx] + v_edges[top_idx+1]) / 2
    top_point = (center_t, top_v)

    # 下顶点：从中心向下找第一个非零
    bot_idx = center_v_idx
    while bot_idx > 0 and counts[bot_idx, center_t_idx] == 0:
        bot_idx -= 1
    bot_v = (v_edges[bot_idx] + v_edges[bot_idx+1]) / 2
    bot_point = (center_t, bot_v)

    # 左顶点：从中心向左找第一个非零
    left_idx = center_t_idx
    while left_idx > 0 and counts[center_v_idx, left_idx] == 0:
        left_idx -= 1
    left_t = (t_edges[left_idx] + t_edges[left_idx+1]) / 2
    left_point = (left_t, center_v)

    # 右顶点：从中心向右找第一个非零
    right_idx = center_t_idx
    while right_idx < counts.shape[1] - 1 and counts[center_v_idx, right_idx] == 0:
        right_idx += 1
    right_t = (t_edges[right_idx] + t_edges[right_idx+1]) / 2
    right_point = (right_t, center_v)

    eye_height = top_v - bot_v
    if eye_height < 0.05:
        return False, np.zeros(8), t, v

    mask_8d = np.array([
        top_point[0], top_point[1]*1000,
        bot_point[0], bot_point[1]*1000,
        left_point[0], left_point[1]*1000,
        right_point[0], right_point[1]*1000
    ], dtype=np.float32)

    return True, mask_8d, t, v

def plot_eye_with_tight_mask(t, v, mask, is_open):
    plt.figure(figsize=(8, 5), dpi=100)

    # ===================== 这里改了！=====================
    # 点更大 + 颜色 blue
    plt.scatter(t, v, s=3.0, color="blue", alpha=0.4)
    # =====================================================

    if is_open:
        top = (mask[0], mask[1]/1000)
        bot = (mask[2], mask[3]/1000)
        left = (mask[4], mask[5]/1000)
        right = (mask[6], mask[7]/1000)

        xs = [top[0], right[0], bot[0], left[0], top[0]]
        ys = [top[1], right[1], bot[1], left[1], top[1]]

        plt.plot(xs, ys, color='red', linewidth=2.5, marker='o', markersize=5, label='菱形MASK')
        plt.fill(xs, ys, color='red', alpha=0.15)

    plt.xlabel("时间 (ps)")
    plt.ylabel("电压 (V)")
    plt.title("眼图 + 贴边菱形MASK")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    csv_path = r"../眼图原始数据集/Eye_001_Z2.50_P120.00_P227.44_A4.02e+11.csv"
    is_open, mask_8d, t_all, v_all = extract_diamond_mask_tight(csv_path)

    print("✅ 眼图是否张开：", is_open)
    print("✅ 贴边菱形MASK 4顶点（ps, mV）：")
    print(np.round(mask_8d, 2))

    plot_eye_with_tight_mask(t_all, v_all, mask_8d, is_open)