import math
def dc_gain(gm, cp, zero, pole1, pole2):
    """
    仅修正单位问题，完全保留你的原始逻辑
    :param gm: 跨导（单位：mS，如35 → 35mS）
    :param cp: 负载电容（单位：pF，如30 → 30pF）
    :param zero: 零点字符串，如 '(-1e9)*(2*pi)'
    :param pole1: 极点1字符串，如 '(-8e9)*(2*pi)'
    :param pole2: 极点2字符串，如 '(-9e9)*(2*pi)'
    :return: 直流增益（线性值）
    """
    # 1. 单位转换：工程单位 → 国际单位
    gm_S = gm * 1e-3  # mS → S（1mS=1e-3S）
    cp_F = cp * 1e-15  # fF → F（1pF=1e-12F）

    # 2. 解析零极点字符串，提取角频率数值（保留你的符号逻辑）
    def parse_omega(freq_str):
        # 替换pi为math.pi，执行公式得到角频率（保留负号）
        freq_fixed = freq_str.replace("pi", "math.pi")
        return eval(freq_fixed)

    omega_z = parse_omega(zero)  # 零点角频率（rad/s）
    omega_p1 = parse_omega(pole1)  # 极点1角频率（rad/s）
    omega_p2 = parse_omega(pole2)  # 极点2角频率（rad/s）

    # 3. 完全保留你的原始计算逻辑，仅替换为转换后的单位
    rs = (2 / gm_S) * (omega_p1 / omega_z - 1)
    cs = (1 / (rs * omega_z))
    rd = 1/(cp_F * omega_p2)
    dcGain = (gm_S * rd) / (1 + gm_S * rs * 0.5)
    print(f"Rs:{rs}")
    print(f"Cs:{cs}")
    print(f"Rd:{rd}")
    print(f"{dcGain}")
    Apre = abs((dcGain * omega_p1 * omega_p2)/omega_z)
    print(f"pre:{Apre}")
    return dcGain


# ---------------------- 按你的参数调用（单位直接传工程值） ----------------------
if __name__ == "__main__":
    # 输入参数：gm=35mS，Cp=30pF，零极点按你的格式
    zero = '(15.999999999e9)*(2*pi)'
    pole1 = '(16e9)*(2*pi)'
    pole2 = '(64e9)*(2*pi)'

    # 调用函数：gm传30（mS）、cp传30（fF）
    dcGain = dc_gain(gm=30, cp=300, zero=zero, pole1=pole1, pole2=pole2)
    print(f"直流增益（线性值）：{dcGain:.8f}")