import pyautogui
import time
import win32gui

# 精准配置（适配你的ADS 2025）
ADS_MAIN_TITLE = "Advanced Design System 2025 (Main)"  # 主窗口完整标题
CONSOLE_SHORTCUT = ["shift", "ctrl", "p"]  # 控制台快捷键
COMMAND = '''
r = design.add_instance(("Basic Components", "R", "symbol"), (0, 0))
r.parameters["R"].value = "100 Ohm"
r.update_item_annotation()
'''


def send_to_ads_console():
    # 1. 直接定位ADS主窗口（跳过枚举，一步到位）
    # FindWindow参数：窗口类名（设为None则按标题匹配）、窗口标题
    ads_hwnd = win32gui.FindWindow(None, ADS_MAIN_TITLE)

    if not ads_hwnd:
        print(f"❌ 未找到ADS主窗口（标题：{ADS_MAIN_TITLE}），请确认ADS已打开！")
        return

    # 强制激活ADS主窗口（前置显示）
    win32gui.SetForegroundWindow(ads_hwnd)
    time.sleep(0.8)  # 等待窗口完全激活

    # 2. 调出Python Console（Shift+Ctrl+P）
    pyautogui.hotkey(*CONSOLE_SHORTCUT)
    time.sleep(0.5)

    # 3. 发送print指令
    pyautogui.typewrite(COMMAND, interval=0.02)
    pyautogui.press("enter")
    print(f"✅ 指令已发送！ADS窗口句柄：{ads_hwnd}")


if __name__ == "__main__":
    send_to_ads_console()