import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 批量画眼图热力图（真正能用版）
def batch_draw_eye(csv_folder, save_folder="eye_images"):
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    os.makedirs(save_folder, exist_ok=True)

    for fname in os.listdir(csv_folder):
        if not fname.endswith(".csv"):
            continue

        path = os.path.join(csv_folder, fname)
        df = pd.read_csv(path)

        # 取数据
        t = df["时间(ps)"]
        v = df["电压(V)"]

        # -------------------- 正确画眼图热力图 --------------------
        plt.figure(figsize=(7, 4), dpi=200)

        #  yout 必须用 hist2d！这才是眼图热力图！
        plt.hist2d(t, v, bins=(200, 100), cmap="jet", cmin=1)

        plt.xlabel("时间 (ps)")
        plt.ylabel("电压 (V)")
        plt.title(f"眼图 {fname}")
        plt.colorbar(label="密度")
        plt.tight_layout()

        # 保存
        save_path = os.path.join(save_folder, fname.replace(".csv", ".png"))
        plt.savefig(save_path)
        plt.close()
        print("已保存：", save_path)

# ===================== 调用 =====================
csv_folder = r"眼图原始数据集"
batch_draw_eye(csv_folder)