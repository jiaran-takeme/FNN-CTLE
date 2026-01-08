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
        self.output_dir = os.path.join(self.workspace_path, r"data/python_data")
        os.makedirs(self.output_dir, exist_ok=True)

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

    def _save_eye_results(self, output_data):
        """
        从仿真结果中提取并保存：
        - 眼图测量指标（Height, Width, Level1, Level0...）
        - 眼图原始数据（time, Density）
        返回 height, width_ps 供外部使用
        """
        # === 1. 找到测量块（含 Height, Width 等）===
        eye_meas_block = None
        for datablock in output_data.find_varblocks_with_var_name("Height"):
            if self.target_probe in datablock.name:
                eye_meas_block = datablock.name
                break
        if not eye_meas_block:
            raise ValueError("未找到眼图测量块（含 Height）")

        # === 2. 找到原始眼图数据块（含 time, Density）===
        eye_raw_block = None
        for datablock in output_data.find_varblocks_with_var_name("Density"):
            if self.target_probe in datablock.name:
                eye_raw_block = datablock.name
                break
        if not eye_raw_block:
            raise ValueError("未找到眼图原始数据块（含 Density）")

        # === 3. 提取测量数据 ===
        my_eye_meas = output_data[eye_meas_block].to_dataframe().reset_index()
        height = float(my_eye_meas["Height"].iloc[0])
        width_s = float(my_eye_meas["Width"].iloc[0])
        level1 = float(my_eye_meas["Level1"].iloc[0])
        level0 = float(my_eye_meas["Level0"].iloc[0])
        width_ps = width_s * 1e12
        amplitude = level1 - level0

        # 构建并保存测量指标 CSV
        meas_data = {
            "指标名称": ["眼高(V)", "眼宽(s)", "眼宽(ps)", "电平1(V)", "电平0(V)", "眼幅(V)"],
            "数值": [height, width_s, width_ps, level1, level0, amplitude]
        }
        df_meas = pd.DataFrame(meas_data)
        meas_csv_filename = os.path.join(
            self.output_dir,
            f"{self.cell_name}_{self.target_probe}_眼图测量指标.csv"
        )
        df_meas.to_csv(meas_csv_filename, index=False, encoding="utf-8-sig")

        # === 4. 提取原始眼图数据 ===
        my_eye_raw = output_data[eye_raw_block].to_dataframe().reset_index()
        df_raw = pd.DataFrame({
            "索引": my_eye_raw["index"],
            "时间(s)": my_eye_raw["time"],
            "时间(ps)": my_eye_raw["time"] * 1e12,
            "密度值": my_eye_raw["Density"]
        })
        raw_csv_filename = os.path.join(
            self.output_dir,
            f"{self.target_probe}_眼图原始数据.csv"
        )
        df_raw.to_csv(raw_csv_filename, index=False, encoding="utf-8-sig")

        return height, width_ps

    def simulate_eye(self, fz, fp1, fp2):
        """
        执行ADS仿真，并自动保存测量指标和原始眼图数据。
        返回：(眼高 V, 眼宽 ps)
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
            simulator.run_netlist(netlist, output_dir=self.output_dir)

            # 读取仿真结果
            ds_path = Path(os.path.join(self.output_dir, f"{self.cell_name}.ds"))
            output_data = dataset.open(ds_path)

            # 保存结果并返回关键指标
            height, width_ps = self._save_eye_results(output_data)
            return height, width_ps

        except Exception as e:
            print(f"仿真出错：{e}")
            return 0.0, 0.0

    def get_raw_eye_data_path(self):
        return os.path.join(self.output_dir, f"{self.target_probe}_眼图原始数据.csv")

    def get_meas_eye_data_path(self):
        return os.path.join(
            self.output_dir,
            f"{self.cell_name}_{self.target_probe}_眼图测量指标.csv"
        )