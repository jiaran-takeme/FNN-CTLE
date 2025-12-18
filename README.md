# FNN-CTLE
常用函数
```python
workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"

de.close_workspace()
de.open_workspace(r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk")
design = db.open_design(name=("FNN_CTLE_lib", "cell_testbench", "schematic"))

design = db.create_schematic("FNN_CTLE_lib:new_lpf:schematic")
design.save_design()
```
## 许可证
具体请参见LICENSE文件

## 联系方式
如有问题或建议，请联系项目维护者。
- 邮箱：1668640479@qq.com
- B 站：祉佲






