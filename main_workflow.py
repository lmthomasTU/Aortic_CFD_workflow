
#import modules
import sys
import os
import os.path as osp
from pathlib import Path
from glob import glob
import numpy as np
import pyvista as pv
import tetgen as tet
import remesh
import utils as ut
import cutting
import volume_mesh
from capping import cap
import identification as id
from tkinter import Tk
from tkinter.filedialog import askdirectory
#----------------------------------------------------------------------------------------------------------------------------
# Setup
#----------------------------------------------------------------------------------------------------------------------------


file_dir = osp.dirname(osp.realpath(__file__))
temp_dir = osp.join(file_dir, r'temp')
output_dir = osp.join(file_dir, r'output')
input_dir = askdirectory(title='Select Input Folder') # shows dialog box and return the path  

os.makedirs(temp_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

inlet_path = osp.join(input_dir, r'inlet.stl')
wall_path = osp.join(input_dir, r'wall.stl')
outlet_path = osp.join(input_dir, r'outlet.stl')

print('Created necessary files and directories')
#paths to the aorta geometry (for standard testing)
#inlet_path = "geometries\input\inlet.stl"
#wall_path = "geometries\input\wall.stl"
#outlet_path = "geometries\input\outlet.stl"

#Reading the files with pyvista
inlet = pv.read(inlet_path)
wall = pv.read(wall_path)
outlet = pv.read(outlet_path)

#Meshing parameters
mmg_parameters = {
    'mesh_density': '0.1',
    'sizing': '1',
    'detection angle': '35'}

tetgen_parameters = dict(
    order=1, 
    mindihedral=20, 
    minratio=1.5)

#Plotting boolean, when True: code generates intermediate plots of workflow
show_plot = True


print('Setup and import done')


#--------------------------------------------------------------------------------------------------------------------------
# 3D-meshing algorithm
#--------------------------------------------------------------------------------------------------------------------------

#Cut the wall geometry after the aortic root
wall_cut = cutting.main_cutter(inlet, wall, plot=show_plot)
pv.save_meshio(osp.join(temp_dir, r'wall_cut.mesh'), wall_cut)

#Create caps
inlet_cap, outlet_cap = cap(wall_cut, plot=show_plot)
pv.save_meshio(osp.join(temp_dir, r'inlet_cap.mesh'), inlet_cap)
pv.save_meshio(osp.join(temp_dir, r'outlet_cap.mesh'), outlet_cap)

#Combine cutted wall and inlet/outlet caps
combined = (wall_cut + inlet_cap + outlet_cap).clean()
print('Meshes succesfully combined')

#Plot result of mesh combining. When edgetest gives an error, the structure has dublicate faces/nodes
if show_plot:
    plt = pv.Plotter()
    plt.add_mesh(combined, style='wireframe')
    edgetest = combined.extract_feature_edges(boundary_edges=True, non_manifold_edges=True, manifold_edges=False, feature_edges=False)
    plt.show()

pv.save_meshio(osp.join(temp_dir, r'combined_mesh.mesh'), combined)



#Run remesh (takes predetermined internally defined file path as input, DON'T CHANGE)
combined_remeshed = remesh.remesh_edge_detect(osp.join(temp_dir, r'combined_mesh.mesh'), osp.join(temp_dir, r'combined_mmg.mesh'), temp_dir, mmg_parameters, plot=show_plot)
#triangulation step to make sure Tetgen only gets triangels as input
combined_remeshed = combined_remeshed.extract_surface().triangulate()


#Make a 3D mesh from the combined mesh
tetmesh = volume_mesh.volume_meshing(combined_remeshed, tetgen_parameters, plot=show_plot)

#Save 3D mesh
tetmesh.save(osp.join(temp_dir, r'3D_output_mesh.vtk'))

#Plot 3D_mesh
if show_plot:
    tetmesh.plot(show_edges = True)

#----------------------------------------------------------------------------------------------------------------------------
# Identification and mapping
#----------------------------------------------------------------------------------------------------------------------------

#From the 3D mesh, select the nodes that belong to the inlet and outlet
inlet_selected = id.selection(tetmesh, inlet_cap)
outlet_selected = id.selection(tetmesh, outlet_cap)

#Plot inlet/outlet of the 3D mesh
if show_plot:
    plt = pv.Plotter()
    plt.add_mesh(inlet_selected, show_edges = True, color = 'red')
    plt.add_mesh(outlet_selected, show_edges = True, color = 'blue')
    plt.show()

#Deletes all the temporary files in the temp folder (have to fix)
""" temp_files = glob(temp_dir)
for f in temp_files:
    os.remove(f) """

print('Done!')

