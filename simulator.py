# simulator.py
import warnings
warnings.filterwarnings("ignore")

from keysight.ads import de
from keysight.ads.de import db_uu as db
import os
from keysight.edatoolbox import ads
import keysight.ads.dataset as dataset
from pathlib import Path
import pandas as pd

# 自定义 pi（避免依赖 math）
pi = 3.141592653


class ADSSimulator:
    def __init__(self, workspace_path, library_name, cell_name, target_probe, gm=35, cp=87):
        self.workspace_path = workspace_path
        self.library_name = library_name
        self.cell_name = cell_name
        self.target_probe = target_probe
        self.gm = gm
        self.cp = cp

    def UCIe(self, zero_list, poles_list):
        """计算增益参数 Apre（字符串形式）"""
        global pi
        wz_val = eval(zero_list[0])
        wp1_val = eval(poles_list[0])
        wp2_val = eval(poles_list[1])
        gm_S = self.gm * 1e-3
        cp_F = self.cp * 1e-15
        Aac = gm_S / (cp_F * wp2_val)
        Adc = (wz_val * Aac) / wp1_val
        Apre = (Adc * wp1_val * wp2_val) / wz_val
        return f"{Apre:.6f}"

    def simulate_eye(self, fz, fp1, fp2):
        """
        执行ADS仿真，返回眼高(V)、眼宽(ps)
        """
        zero = [f"(-{fz}e9)*(2*pi)"]
        poles = [f"(-{fp1}e9)*(2*pi)", f"(-{fp2}e9)*(2*pi)"]
        Apre = self.UCIe(zero, poles)

        try:
            design = db.open_design(name=(self.library_name, self.cell_name, "schematic"))
            rx_diff1 = design.find_instance("Rx_Diff1")
            rx_diff1.parameters['Gain'].value = Apre
            rx_diff1.parameters['Zero'].value = zero
            rx_diff1.parameters['Pole'].value = poles
            rx_diff1.update_item_annotation()

            netlist = design.generate_netlist()
            simulator = ads.CircuitSimulator()
            target_output_dir = os.path.join(self.workspace_path, r"data/python_data")
            os.makedirs(target_output_dir, exist_ok=True)
            simulator.run_netlist(netlist, output_dir=target_output_dir)

            output_data = dataset.open(Path(os.path.join(target_output_dir, f"{self.cell_name}.ds")))

            eye_meas_block = None
            for datablock in output_data.find_varblocks_with_var_name("Height"):
                if self.target_probe in datablock.name:
                    eye_meas_block = datablock.name
                    break
            if not eye_meas_block:
                raise ValueError("未找到眼图测量块")

            my_eye_meas = output_data[eye_meas_block].to_dataframe().reset_index()
            height = my_eye_meas["Height"].iloc[0]
            width_s = my_eye_meas["Width"].iloc[0]
            width_ps = width_s * 1e12

            return height, width_ps

        except Exception as e:
            print(f"仿真出错：{e}")
            return 0.0, 0.0

    def get_raw_eye_data_path(self):
        target_output_dir = os.path.join(self.workspace_path, r"data/python_data")
        return os.path.join(target_output_dir, f"{self.target_probe}_眼图原始数据.csv")