import math  # 导入math库，提供pi常量

# 定义参数（保持原有单位定义）
gm = 35  # mS (毫西门子)
cp = 87  # fF (飞法)
wz = "(5.44e9)*(2*math.pi)"  # 修正：使用math.pi，否则会报pi未定义
wp1 = "(16.69e9)*(2*math.pi)"
wp2 = "(48e9)*(2*math.pi)"


def PCIe(gm, cp, wz, wp1, wp2):
    # 第一步：将字符串表达式解析为数值
    # eval()会执行字符串中的数学运算，得到具体的数值
    wz_val = eval(wz)
    wp1_val = eval(wp1)
    wp2_val = eval(wp2)

    # 第二步：单位转换（关键！原有代码未处理单位，结果会偏差）
    # gm: mS(毫西门子) -> S(西门子)：1 mS = 1e-3 S
    gm_S = gm * 1e-3
    # cp: fF(飞法) -> F(法拉)：1 fF = 1e-15 F
    cp_F = cp * 1e-15

    # 第三步：计算各项参数
    Aac = gm_S / (cp_F * wp2_val)
    Adc = (wz_val * Aac) / wp1_val
    Apre = (Adc * wp1_val * wp2_val) / wz_val

    # 打印结果（保留4位小数，便于阅读）
    print(f"Aac: {Aac:.4f}")
    print(f"Adc: {Adc:.4f}")
    return Apre


# 调用函数并打印最终结果
Apre = PCIe(gm=gm, cp=cp, wz=wz, wp1=wp1, wp2=wp2)
print(f"Apre: {Apre:.4f}")