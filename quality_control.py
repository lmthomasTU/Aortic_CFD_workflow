import pyvista as pv

def meshreport(mesh, text):
    # Calculate mesh stats and quality
    jac = mesh.compute_cell_quality(quality_measure='scaled_jacobian')['CellQuality']
    aspect = mesh.compute_cell_quality(quality_measure='aspect_ratio')['CellQuality']
    num_points = mesh.number_of_points
    num_cells = mesh.number_of_cells

    # Print report
    print('--------------------------------------------------------------')
    print(text)
    print('num points:', num_points)
    print('num_cells: ', num_cells)
    print('Mesh quality (mean scaled jacobian)')
    print('min:', jac.min())
    print('max:', jac.max())
    print('avg:', jac.mean())
    print('Mesh quality (aspect ratio)')
    print('min:', aspect.min())
    print('max:', aspect.max())
    print('avg:', aspect.mean())
    print('--------------------------------------------------------------')
    report = {'jac':jac,'aspect':aspect, 'points':num_points, 'cells':num_cells} 

    #Create report text for log files
    report_text = '''
    --------------------------------------------------------------
    {0}
    num points: {1}
    num_cells: {2}
    Mesh quality (mean scaled jacobian)
    min: {3}
    max: {4}
    avg: {5}
    Mesh quality (aspect ratio)
    min: {6}
    max: {7}
    avg: {8}
    --------------------------------------------------------------
    '''.format(text, num_points, num_cells, jac.min(), jac.max(), jac.mean(), aspect.min(), aspect.max(), aspect.mean())


    return report, report_text

def clip_plot(mesh, text):
    # Plots a geometry clipped along the z axis to show the inside mesh
    surf = mesh.extract_surface()
    clipped = mesh.clip('z', crinkle=True)

    plotter = pv.Plotter()
    plotter.add_mesh(clipped, 'lightgrey', lighting=True, show_edges=True)
    plotter.add_mesh(surf, 'r', 'wireframe')
    plotter.add_legend([['Mesh surface', 'r'], ['Clipped mesh', 'black']])
    plotter.add_text(text)
    plotter.show()