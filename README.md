# FNN-CTLE
常用函数
```python
# 路径
workspace_path = r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk"
cell_name = "cell_testbench"
library_name = "FNN_CTLE_lib"
# 常用函数
de.close_workspace()
de.open_workspace(r"C:/Users/zhaohongrui/Desktop/ADS/FNN_CTLE_wrk")
design = db.open_design(name=("FNN_CTLE_lib", "cell_testbench", "schematic"))

# 常用库
from keysight.ads import de
from keysight.ads.de import db_uu as db
import os

from keysight.edatoolbox import ads
 # 仿真相关
netlist = design.generate_netlist()
print(netlist)
simulator = ads.CircuitSimulator()
target_output_dir = os.path.join(workspace_path, "data")
simulator.run_netlist(netlist, output_dir=target_output_dir)
# 数据处理
import keysight.ads.dataset as dataset
import matplotlib.pyplot as plt
from IPython.core import getipython
from pathlib import Path
import numpy as np
```
## 许可证
具体请参见LICENSE文件

## 联系方式
如有问题或建议，请联系项目维护者。
- 邮箱：1668640479@qq.com
- B 站：祉佲






