import win32com.client as win32

# 启动ADS
ads_app = win32.Dispatch("ADS.Application")
ads_app.Visible = True  # 显示ADS界面（可选）

# 打开已有的ADS工程
proj_path = r"C:\Your\ADS\Project\YourProject.adsn"
proj = ads_app.OpenProject(proj_path)

# 打开目标原理图
schematic_name = "YourSchematic"  # 原理图名称
schematic = proj.Schematics.Item(schematic_name)
schematic.Visible = True