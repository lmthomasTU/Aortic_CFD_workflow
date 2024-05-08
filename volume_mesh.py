import pyvista as pv
import tetgen as tet

def volume_meshing(combined_mesh, tetgen_parameters, show_plot):

    print('Start 3D-meshing')
    # create 3D tetmesh from surface mesh
    tetmesh = tet.TetGen(combined_mesh)
    tetmesh.tetrahedralize(**tetgen_parameters)
    grid = tetmesh.grid
    

    print('3D meshing succesfull')
    if show_plot == True:
        grid.plot(show_edges=True)

        # Save the generated mesh as a .stl
        grid.save('aorta_tetmesh.vtk', binary=False)

        # get cell centroids
        cells = grid.cells.reshape(-1, 5)[:, 1:]
        cell_center = grid.points[cells].mean(1)

        # extract cells below the 0 xy plane
        mask = cell_center[:, 2] < 0
        cell_ind = mask.nonzero()[0]
        subgrid = grid.extract_cells(cell_ind)

        # advanced plotting
        plotter = pv.Plotter()
        plotter.add_mesh(subgrid, 'lightgrey', lighting=True, show_edges=True)
        plotter.add_mesh(combined_mesh, 'r', 'wireframe')
        plotter.add_legend([[' Input Mesh ', 'r'],
                            [' Tessellated Mesh ', 'black']])
        plotter.show()

    return grid