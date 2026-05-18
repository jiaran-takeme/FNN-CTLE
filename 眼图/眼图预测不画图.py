# -*- coding: utf-8 -*-
"""
CTLE 眼图预测：零极点 + Apre → 眼高 / 眼宽（PyTorch 正确版）
保留所有样本，包括眼高/眼宽=0（未睁开眼图）
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

import torch
import torch.nn as nn
import torch.optim as optim

# ===================== 中文画图支持 =====================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# ===================== 控制训练集数量 =====================
USE_TRAIN_SAMPLES = 1000
# ===========================================================================

# ===================== 1. 读取数据（不筛选！全部保留） =====================
df = pd.read_excel("眼图数据集.xlsx")

# 限制数量（如果需要）
if USE_TRAIN_SAMPLES is not None:
    df = df.head(USE_TRAIN_SAMPLES)
    print(f"✅ 已限制使用前 {USE_TRAIN_SAMPLES} 组数据训练")

print(f"✅ 最终训练数据集总数：{len(df)} 组")
print(f"✅ 包含眼图睁开 + 未睁开（眼高/眼宽=0）全部样本")

# 输入：zero, pole1, pole2, Apre
X = df[["zero(GHz)", "pole1(GHz)", "pole2(GHz)", "Apre"]].values
# 输出：眼高, 眼宽（包含 0 值）
y = df[["眼高(V)", "眼宽(ps)"]].values

# ===================== 2. 数据标准化 =====================
scaler_X = StandardScaler()
scaler_y = StandardScaler()

X = scaler_X.fit_transform(X)
y = scaler_y.fit_transform(y)

# 训练集 / 测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ===================== 3. 转为 PyTorch 张量 =====================
X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test  = torch.tensor(X_test, dtype=torch.float32)
y_test  = torch.tensor(y_test, dtype=torch.float32)

# ===================== 4. 构建网络 =====================
class EyeNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 2)
        )

    def forward(self, x):
        return self.net(x)

model = EyeNet()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# ===================== 5. 训练 =====================
epochs = 500
train_losses = []
test_losses = []

for epoch in range(epochs):
    model.train()
    pred = model(X_train)
    loss = criterion(pred, y_train)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    model.eval()
    with torch.no_grad():
        pred_test = model(X_test)
        loss_test = criterion(pred_test, y_test)

    train_losses.append(loss.item())
    test_losses.append(loss_test.item())

    if epoch % 50 == 0:
        print(f"Epoch {epoch:3d} | 训练loss: {loss.item():.6f} | 测试loss: {loss_test.item():.6f}")

# ===================== 6. 预测 & 反归一化 =====================
model.eval()
with torch.no_grad():
    y_pred = model(X_test).numpy()

y_true = scaler_y.inverse_transform(y_test.numpy())
y_pred = scaler_y.inverse_transform(y_pred)

# ===================== 7. 评估指标 =====================
r2_height = r2_score(y_true[:, 0], y_pred[:, 0])
r2_width  = r2_score(y_true[:, 1], y_pred[:, 1])

print("\n" + "=" * 60)
print("✅ 模型预测精度（包含未睁开眼图）")
print(f"眼高预测 R²: {r2_height:.4f}")
print(f"眼宽预测 R²: {r2_width:.4f}")
print("=" * 60)

# ===================== 1. 训练损失曲线 =====================
plt.figure(figsize=(10, 4))
plt.plot(train_losses, label='训练损失', linewidth=2)
plt.plot(test_losses, label='测试损失', linewidth=2)
plt.xlabel('Epoch')
plt.ylabel('Loss (MSE)')
plt.title('训练曲线 - 损失变化')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ===================== 2. 真实值 vs 预测值 对比图 =====================
plt.figure(figsize=(12, 5))

# 左图：眼高
plt.subplot(1, 2, 1)
plt.scatter(y_true[:, 0], y_pred[:, 0], alpha=0.7, color='#4285F4')
min_h = min(y_true[:,0].min(), y_pred[:,0].min())
max_h = max(y_true[:,0].max(), y_pred[:,0].max())
plt.plot([min_h, max_h], [min_h, max_h], 'r--', linewidth=2, label='完美预测')
plt.xlabel('真实眼高 (V)')
plt.ylabel('预测眼高 (V)')
plt.title(f'眼高预测  $R^2$ = {r2_height:.4f}')
plt.legend()
plt.grid(alpha=0.3)

# 右图：眼宽
plt.subplot(1, 2, 2)
plt.scatter(y_true[:, 1], y_pred[:, 1], alpha=0.7, color='#34A853')
min_w = min(y_true[:,1].min(), y_pred[:,1].min())
max_w = max(y_true[:,1].max(), y_pred[:,1].max())
plt.plot([min_w, max_w], [min_w, max_w], 'r--', linewidth=2, label='完美预测')
plt.xlabel('真实眼宽 (ps)')
plt.ylabel('预测眼宽 (ps)')
plt.title(f'眼宽预测  $R^2$ = {r2_width:.4f}')
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()
plt.show()

# ===================== 8. 预测函数 =====================
def predict_eye(zero, pole1, pole2, Apre):
    x = np.array([[zero, pole1, pole2, Apre]])
    x = scaler_X.transform(x)
    x = torch.tensor(x, dtype=torch.float32)

    model.eval()
    with torch.no_grad():
        pred = model(x).numpy()

    pred = scaler_y.inverse_transform(pred)
    height = pred[0, 0]
    width  = pred[0, 1]
    return height, width

# ===================== 测试 =====================
if __name__ == "__main__":
    print("\n🎯 测试预测：")
    h, w = predict_eye(5.0, 18.0, 30.0, 3.2e11)
    print(f"眼高 = {h:.4f} V")
    print(f"眼宽 = {w:.2f} ps")