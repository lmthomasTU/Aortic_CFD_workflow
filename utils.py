import sys
import os
from os.path import join
import numpy as np
from itertools import groupby
from collections import Counter
import re
from scipy import interpolate
from scipy.interpolate import RBFInterpolator, NearestNDInterpolator
from scipy.spatial import distance
import pyvista as pv


def rotation_matrix_from_vectors(vec1, vec2):
    """ Find the rotation matrix that aligns vec1 to vec2
    :param vec1: A 3d "source" vector
    :param vec2: A 3d "destination" vector
    :return mat: A transform matrix (3x3) which when applied to vec1, aligns it with vec2.
    """
    a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
    v = np.cross(a, b)
    c = np.dot(a, b)
    s = np.linalg.norm(v)
    kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    rotation_matrix = np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))
    return rotation_matrix



# core function for interpolating profiles in 3D space
def interpolate_profiles(aligned_planes, fxdpts, intp_options):
    num_frames = len(aligned_planes)

    # Set boundary vectors to zero
    dr = intp_options['zero_boundary_dist']  # percentage threshold for zero boundary
    edges = [aligned_planes[k].extract_feature_edges().connectivity() for k in range(num_frames)]
    large_edge_id = [np.argmax(np.bincount(edges[k]['RegionId'])) for k in range(num_frames)]
    edge_pts = [edges[k].points[np.where(edges[k]['RegionId'] == large_edge_id[k])] for k in range(num_frames)]
    #edge_pts = [aligned_planes[k].extract_feature_edges(boundary_edges=True, feature_edges=False, manifold_edges=False).points for k in range(num_frames)]
    dist2edge = [distance.cdist(aligned_planes[k].points, edge_pts[k]).min(axis=1) for k in range(num_frames)]
    boundary_ids = [np.where(dist2edge[k] < (dr * dist2edge[k].max()))[0] for k in range(num_frames)]
    for k in range(num_frames):
        aligned_planes[k]['Velocity'][boundary_ids[k], :] = 0.0

    # Set backflow to zero
    if intp_options['zero_backflow']:
        normals = [aligned_planes[k].compute_normals()['Normals'].mean(0) * -1 for k in
                   range(num_frames)]  # Careful with the sign
        normals = [normals[k] / np.linalg.norm(normals[k]) for k in range(num_frames)]
        for k in range(num_frames):
            signs = np.dot(aligned_planes[k]['Velocity'], normals[k])
            aligned_planes[k]['Velocity'][np.where(signs < 0)] = 0.0

    # interpolate velocity profile
    vel_interp = []
    # print('fitting...')
    for k in range(num_frames):
        nnVel = NearestNDInterpolator(aligned_planes[k].points, aligned_planes[k]['Velocity'])(fxdpts)
        I = RBFInterpolator(fxdpts, nnVel,
                            kernel=intp_options['kernel'], smoothing=intp_options['smoothing'],
                            epsilon=1, degree=intp_options['degree'])

        vel_interp.append(I(fxdpts))

    # hard no slip condition (double check)
    if intp_options['hard_noslip']:
        for k in range(num_frames):
            vel_interp[k][boundary_ids, :] = 0

    # create new polydatas
    interp_planes = [pv.PolyData(fxdpts).delaunay_2d(alpha=0.1) for _ in range(num_frames)]
    for k in range(num_frames):
        interp_planes[k]['Velocity'] = vel_interp[k]

    return interp_planes



def rotation_matrix_from_axis_and_angle(u, theta):
    """:arg u is axis (3 components)
       :arg theta is angle (1 component) obtained by acos of dot prod
    """

    from math import cos, sin

    R = np.asarray([[cos(theta) + u[0] ** 2 * (1 - cos(theta)),
             u[0] * u[1] * (1 - cos(theta)) - u[2] * sin(theta),
             u[0] * u[2] * (1 - cos(theta)) + u[1] * sin(theta)],
            [u[0] * u[1] * (1 - cos(theta)) + u[2] * sin(theta),
             cos(theta) + u[1] ** 2 * (1 - cos(theta)),
             u[1] * u[2] * (1 - cos(theta)) - u[0] * sin(theta)],
            [u[0] * u[2] * (1 - cos(theta)) - u[1] * sin(theta),
             u[1] * u[2] * (1 - cos(theta)) + u[0] * sin(theta),
             cos(theta) + u[2] ** 2 * (1 - cos(theta))]])

    return R

def mesh_quality(startmesh, remesh, meshname='', plot=False):
    '''
    Function to assess the quality of a surface mesh. Two factors are consdidered: similarity to the input in terms of shape
    and quality of the elements of the remesh.
    The first metric is based on the smallest distance between each node of the starting mesh and the surface of the remesh
    The second metric is based on the scaled jacobian of eacht cell element


    startmesh: (pyvista.PolyData)
    remesh: (pyvista.Polydata)
    meshname: (str) Name for the comparison, use to keep oversight if running the function multiple times
    plot: (bool) Show 3D plots of the quality and similarity

    Returns: (mean_similarity(#lower is better), mean_quality)
    '''
    closest_cells, closest_points = remesh.find_closest_cell(startmesh.points, return_closest_point=True)
    d_exact = np.linalg.norm(startmesh.points - closest_points, axis=1)
    startmesh.point_data['absdistance'] = d_exact
    quality = remesh.compute_cell_quality()
    mean_similarity = np.mean(d_exact)
    mean_quality = np.mean(quality.cell_data['CellQuality'])
    print('Mean similarity of',meshname,'(lower is better) =', mean_similarity)
    print('Mean quality of',meshname,' =', mean_quality)
    if plot==True:
        startmesh.plot(text=(meshname +' similarity to original mesh'))
        quality.plot(text=('Cell quality of ' + meshname))
    return(mean_similarity, mean_quality)