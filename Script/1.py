from keysight.ads import de
from keysight.ads.de import db_uu as db
import os

workspace_path =r"C:\Users\zhaohongrui\Desktop\ADS\FNN_CTLE_wrk"
cell_name = "cell_channel"
library_name = "FNN_CTLE_lib"


def create_and_open_an_empty_workspace(workspace_path: str):
    # Ensure there isn't already a workspace open
    if de.workspace_is_open():
        de.close_workspace()

    # Cannot create a workspace if the directory already exists
    # Cannot create a workspace if the directory already exists
    if os.path.exists(workspace_path):
        raise RuntimeError(f"Workspace directory already exists: {workspace_path}")

    # Create the workspace
    workspace = de.create_workspace(workspace_path)
    # Open the workspace
    workspace.open()
    # Return the open workspace and close when it finished
    return workspace


def create_a_library_and_add_it_to_the_workspace(workspace: de.Workspace):
    # assert workspace.path is not None
    # Libraries can only be added to an open workspace
    assert workspace.is_open
    # We'll create a library in the directory of the workspace
    library_path = workspace.path / library_name
    # Create the library
    de.create_new_library(library_name, library_path)
    # And add it to the workspace (update lib.defs)
    workspace.add_library(library_name, library_path, de.LibraryMode.SHARED)
    lib = workspace.open_library(library_name, library_path, de.LibraryMode.SHARED)
    lib.setup_schematic_tech()
    return lib


ws = create_and_open_an_empty_workspace(workspace_path)
# Create and add library to the empty workspace using the pointer to the workspace
lib = create_a_library_and_add_it_to_the_workspace(ws)


def create_schematic(library: de.Library):
    design = db.create_schematic(f"{library_name}:{cell_name}:schematic")

    num_inds = 5
    num_caps = num_inds - 1

    for i in range(num_inds):
        ind = design.add_instance("ads_rflib:L:symbol", (i * 2, 0))
        ind.parameters["L"].value = "70 nH"
        ind.update_item_annotation()
        design.add_wire([(i * 2 + 1, 0), (i * 2 + 2, 0)])

    for i in range(num_caps):
        cap = design.add_instance("ads_rflib:C:symbol", (i * 2 + 1.5, -1), angle=-90)
        cap.parameters["C"].value = "30 pF"
        cap.update_item_annotation()
        design.add_wire([(i * 2 + 1.5, 0), (i * 2 + 1.5, -1)])
        design.add_instance("ads_rflib:GROUND:symbol", (i * 2 + 1.5, -2), angle=-90)

    design.add_instance("ads_simulation:TermG:symbol", (-1, -1), angle=-90)
    design.add_instance("ads_simulation:TermG:symbol", (10, -1), angle=-90)

    design.add_wire([(-1, -1), (-1, 0), (0, 0)])
    design.add_wire([(10, -1), (10, 0)])

    sp = design.add_instance("ads_simulation:S_Param:symbol", (0, 2))
    sp.parameters["Start"].value = "0.01 GHz"
    sp.parameters["Stop"].value = "0.5 GHz"
    sp.parameters["Step"].value = "0.001 GHz"
    sp.update_item_annotation()
    design.save_design()
    return design


# Create schematic with the lib object/pointer
design = create_schematic(lib)

### Netlist Creation and Simulation ###
from keysight.edatoolbox import ads

netlist = design.generate_netlist()
print(netlist)
simulator = ads.CircuitSimulator()
target_output_dir = os.path.join(workspace_path, "data")
simulator.run_netlist(netlist, output_dir=target_output_dir)

##### Data Processing & Plot #####

import keysight.ads.dataset as dataset
import matplotlib.pyplot as plt
from IPython.core import getipython
from pathlib import Path
import numpy as np

output_data = dataset.open(Path(os.path.join(target_output_dir, f"{cell_name}" + ".ds")))

# Inspect available data blocks in the dataset
print(output_data.varblock_names)

# Convert SP1.SP datablock to the pandas dataframe
mydata = output_data["SP1.SP"].to_dataframe().reset_index()
print(mydata)

# Extract data and convert S21 & S11 to dB
freq = mydata["freq"] / 1e6
S21 = 20 * np.log10(abs(mydata["S[2,1]"]))
S11 = 20 * np.log10(abs(mydata["S[1,1]"]))

# Plot results using inline plot from matplotlib
ipython = getipython.get_ipython()
ipython.run_line_magic("matplotlib", "inline")
_, ax = plt.subplots()
ax.set_title("Python Filter Response")
plt.xlabel("Frequency (MHz)")
plt.ylabel("S21 and S11 (dB)")
plt.grid(True)
plt.plot(freq, S21)
plt.plot(freq, S11)