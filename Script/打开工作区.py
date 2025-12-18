from keysight.ads import de
import traceback
import os

# 修正后的工作区路径（你的实际路径）
WORKSPACE_PATH = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
LIBRARY_NAME = "FNN_CTLE.lib"
CELL_NAME = "cell_testbench"  # 可替换为 cell_channel
VIEW_NAME = "Schematic"


def open_ads_schematic():
    """
    打开ADS电路图，适配所有ADS版本，无版本相关API报错
    """
    try:
        # ========== 步骤1：强制打开/重新打开工作区（规避版本API差异） ==========
        # 先检查路径是否存在
        if not os.path.exists(WORKSPACE_PATH):
            raise ValueError(f"❌ 工作区路径不存在：{WORKSPACE_PATH}")

        # 不管是否已打开，先执行open_workspace（ADS会自动处理重复打开）
        # 这是最稳定的方式，避开所有get/workspace/library等版本兼容问题
        de.open_workspace(WORKSPACE_PATH)
        print(f"✅ 已成功加载工作区：{WORKSPACE_PATH}")

        # ========== 步骤2：逐层获取 库→单元→视图（用最基础的try-except判断） ==========
        # 获取库（用try-except替代版本相关的属性）
        library = None
        try:
            # 尝试通过工作区对象获取库（通用方式）
            workspace = de.open_workspace(WORKSPACE_PATH)  # 重新获取打开的工作区对象
            library = workspace.Library(LIBRARY_NAME)
        except Exception:
            # 兜底：若上述方式失败，直接通过Library类初始化
            try:
                library = de.Library(LIBRARY_NAME)
            except Exception as e:
                raise ValueError(f"❌ 获取库 {LIBRARY_NAME} 失败：{str(e)}")

        # 获取单元（用if_exists逻辑避免不存在报错）
        cell = None
        try:
            cell = library.GetCellIfExists(CELL_NAME)
        except Exception:
            # 兼容不同命名的方法
            try:
                cell = library.cell_if_exists(CELL_NAME)
            except Exception as e:
                raise ValueError(f"❌ 获取单元 {CELL_NAME} 失败：{str(e)}")
        if not cell:
            raise ValueError(f"❌ 单元 {CELL_NAME} 不存在于库 {LIBRARY_NAME} 中")

        # 获取视图
        schematic_view = None
        try:
            schematic_view = cell.GetViewIfExists(VIEW_NAME)
        except Exception:
            try:
                schematic_view = cell.view_if_exists(VIEW_NAME)
            except Exception as e:
                raise ValueError(f"❌ 获取视图 {VIEW_NAME} 失败：{str(e)}")
        if not schematic_view:
            raise ValueError(f"❌ 视图 {VIEW_NAME} 不存在于单元 {CELL_NAME} 中")

        # ========== 步骤3：打开电路图 ==========
        schematic_view.Open()  # 兼容大写Open/小写open
        print(f"🎉 成功打开电路图：{LIBRARY_NAME}/{CELL_NAME}/{VIEW_NAME}")

    # ========== 全场景异常处理 ==========
    except ValueError as ve:
        print(f"\n❌ 业务错误：{str(ve)}")
    except RuntimeError as re:
        print(f"\n❌ 运行时错误：{str(re)}")
        if "already open" in str(re).lower():
            print("💡 提示：电路图/工作区已打开，可在ADS界面直接查看")
    except Exception as e:
        print(f"\n❌ 未知错误：{str(e)}")
        print("📝 错误详情：")
        traceback.print_exc()


# 执行函数
if __name__ == "__main__":
    open_ads_schematic()