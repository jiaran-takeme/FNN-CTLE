# -*- coding: utf-8 -*-
"""
贝叶斯优化 CTLE 训练日志可视化
功能：读取 optimization_history.csv 并绘制得分与眼高随轮次变化的曲线
"""

import pandas as pd
import matplotlib.pyplot as plt

# ==================== 配置 ====================
CSV_FILE = "optimization_history.csv"  # 日志文件名
OUTPUT_FIG = "training_log.png"        # 输出图像文件名（可选）

# ==================== 主程序 ====================
def main():
    # 1. 加载数据
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
    except FileNotFoundError:
        print(f"❌ 错误：未找到文件 '{CSV_FILE}'，请确保它与本脚本在同一目录。")
        return
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        return

    # 2. 按评估轮次排序（确保顺序正确）
    df = df.sort_values('eval').reset_index(drop=True)

    # 3. 提取关键数据
    evals = df['eval']
    scores = df['score']
    eye_heights = df['eye_height_V']

    # 4. 找到全局最优解
    best_idx = scores.idxmax()
    best_score = scores.iloc[best_idx]
    best_eval = evals.iloc[best_idx]

    # 5. 设置中文字体（兼容 Windows / macOS / Linux）
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

    # 6. 绘图
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # --- 左侧 Y 轴：综合得分 ---
    color_score = '#1f77b4'  # 蓝色
    ax1.set_xlabel('优化轮次 (Evaluation)', fontsize=12)
    ax1.set_ylabel('综合得分 (Score)', color=color_score, fontsize=12)
    line1 = ax1.plot(evals, scores, color=color_score, marker='o', markersize=4, label='综合得分')
    ax1.tick_params(axis='y', labelcolor=color_score)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 在最优得分点添加注释
    ax1.annotate(
        f'最优得分: {best_score:.4f}\n(第 {int(best_eval)} 轮)',
        xy=(best_eval, best_score),
        xytext=(best_eval + 5, best_score - 0.08),
        arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
        fontsize=10,
        color='red',
        weight='bold',
        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5)
    )

    # --- 右侧 Y 轴：眼高 ---
    ax2 = ax1.twinx()
    color_height = '#2ca02c'  # 绿色
    ax2.set_ylabel('眼高 (Eye Height / V)', color=color_height, fontsize=12)
    line2 = ax2.plot(evals, eye_heights, color=color_height, marker='s', markersize=3, alpha=0.7, label='眼高')
    ax2.tick_params(axis='y', labelcolor=color_height)

    # --- 图例与标题 ---
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='lower right', fontsize=10)

    plt.title('贝叶斯优化训练日志', fontsize=14, weight='bold', pad=20)

    # 7. 保存并显示
    plt.tight_layout()
    plt.savefig(OUTPUT_FIG, dpi=200, bbox_inches='tight')
    print(f"✅ 图像已保存为: {OUTPUT_FIG}")
    plt.show()

if __name__ == "__main__":
    main()