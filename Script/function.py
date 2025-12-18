from keysight.ads import de
import os

workspace_path = "C:/ADS_Python_Tutorials/tutorial1_wrk"


def create_and_open_an_empty_workspace(workspace_path: str):
    # Ensure there isn't already a workspace open
    if de.workspace_is_open():
        de.close_workspace()

    # Cannot create a workspace if the directory already exists
    if os.path.exists(workspace_path):
        raise RuntimeError(f"Workspace directory already exists: {workspace_path}")

    # Create the workspace
    workspace = de.create_workspace(workspace_path)
    # Open the workspace
    workspace.open()
    # Return the open workspace and close when it finished
    return workspace


def create_a_library_and_add_it_to_the_workspace(workspace: de.Workspace) -> None:
    # assert workspace.path is not None
    # Libraries can only be added to an open workspace
    assert workspace.is_open
    # We'll create a library in the directory of the workspace
    library_name = "tutorial1_lib"
    library_path = workspace.path / library_name
    # Create the library
    de.create_new_library(library_name, library_path)
    # And add it to the workspace (update lib.defs)
    workspace.add_library(library_name, library_path, de.LibraryMode.SHARED)
    lib = workspace.open_library(library_name, library_path, de.LibraryMode.SHARED)
    return lib


# Create empty workspace and "ws" object/pointer
ws = create_and_open_an_empty_workspace(workspace_path)
# Create and add library to the empty workspace using the pointer to the workspace
lib = create_a_library_and_add_it_to_the_workspace(ws)

design = db.create_schematic("tutorial1_lib:python_schematic:schematic")

# Alternatively, you can use the library pointer
# design = db.create_schematic(f"{lib.name}:python_schematic:schematic")

# Insert a resistor & create a pointer
r = design.add_instance(("ads_rflib", "R", "symbol"), (0, 0))
r.parameters["R"].value = "100 Ohm"
r.update_item_annotation()

# Insert another resistor with 90deg rotation but no pointer
design.add_instance("ads_rflib:R:symbol", (2, 0), name="myR", angle=-90)

# Draw wire to connect both the resistors
design.add_wire([(1, 0), (2, 0)])

# Logic to create a pointer to a instance in the design and then update its value
myr = design.instances.get("myR")
myr.parameters["R"].value = "1000 Ohm"
myr.update_item_annotation()

# Function to iterate through all instanaces in the design, search for a specific
# component and then modify the value
for inst in design.instances:
    print(inst)
    if inst.name == "myR":
        inst.parameters["R"].value = "100 Ohm"
        inst.update_item_annotation()
        print("Instance value is updated")

# Iterate though instances and print model definition parameters for each of them
for inst in design.instances:
    print(inst.model_def.parameters)

# Create a LC ladder network with a for loop
num_inds = 5
num_caps = num_inds - 1

for i in range(num_inds):
    ind = design.add_instance("ads_rflib:L:symbol", (i * 2, -2))
    ind.parameters["L"].value = "70 nH"
    ind.update_item_annotation()
    design.add_wire([(i * 2 + 1, -2), (i * 2 + 2, -2)])

for i in range(num_caps):
    cap = design.add_instance("ads_rflib:C:symbol", (i * 2 + 1.5, -3), angle=-90)
    cap.parameters["C"].value = "30 pF"
    cap.update_item_annotation()
    design.add_wire([(i * 2 + 1.5, -2), (i * 2 + 1.5, -3)])
    design.add_instance("ads_rflib:GROUND:symbol", (i * 2 + 1.5, -4), angle=-90)

design.save_design()

from keysight.ads import de
from keysight.ads.de import db_uu as db
import os