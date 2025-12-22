import sys
import os
import platform

# ========== 保留之前的环境变量+路径配置（无需改） ==========
ADS_PATH = r"D:\ProgramFiles\Keysight\ADS2025"
os.environ["HPEESOF_DIR"] = ADS_PATH
os.environ["HPEESOF_ROOT"] = ADS_PATH
os.environ["PATH"] = f"{ADS_PATH}\\bin;{ADS_PATH}\\tools\\python;{os.environ['PATH']}"
os.environ["PYTHONHOME"] = sys.prefix

for p in sys.path[:]:
    if "Keysight" in p or "ADS2025" in p:
        sys.path.remove(p)
sys.path.insert(0, os.path.join(ADS_PATH, "tools", "python"))
sys.path.insert(0, os.path.join(ADS_PATH, "tools", "python", "Lib"))
sys.path.insert(0, os.path.join(ADS_PATH, "tools", "python", "Lib", "site-packages"))
sys.path.insert(0, os.path.join(ADS_PATH, "bin"))
sys.path.insert(0, os.path.join(ADS_PATH, "oalibs"))

# ========== 关键修改：删除旧模块导入，直接导入keysight.ads ==========
try:
    # 跳过ads_common/ads_dataset，直接导入新版模块
    from keysight.ads import de
    from keysight.ads.de import db_uu as db
    from keysight.edatoolbox import ads
    import keysight.ads.dataset as dataset
    print("=== ✅ 所有ADS库导入成功！ ===")
except ImportError as e:
    print(f"=== ❌ 导入失败：{str(e)} ===")
    # 调试：打印keysight下的子模块
    import keysight  # 先导入顶层模块
    print("=== keysight下的子模块 ===")
    for mod in dir(keysight):
        if not mod.startswith("_"):
            print(f"keysight.{mod}")
    raise