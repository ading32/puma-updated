from pumapy.physicsmodels.mpsa_elasticity import Elasticity
from pumapy.physicsmodels.property_maps import ElasticityMap
from pumapy.utilities.workspace import Workspace
import numpy as np
import pyvista as pv


def compute_elasticity(workspace, elast_map, direction, side_bc='p', tolerance=1e-4,
                       maxiter=100000, solver_type='gmres', display_iter=True):
    """ Compute the effective elasticity coefficient
        (N.B. 0 material ID in workspace refers to air unless otherwise specified)

        :param workspace: domain
        :type workspace: pumapy.Workspace
        :param elast_map: local elasticity of the constituents
        :type elast_map: pumapy.ElasticityMap
        :param direction: direction for solve ('x','y', 'z', 'yz', 'xz', 'xy')
        :type direction: string
        :param side_bc: side boundary conditions can be symmetric ('s'), periodic ('p'), dirichlet ('d') or free ('f')
        :type side_bc: string
        :param tolerance: tolerance for iterative solver
        :type: tolerance: float
        :param maxiter: maximum Iterations for solver
        :type maxiter: int
        :param solver_type: solver type, options: 'gmres' (default), 'bicgstab', 'direct'
        :type solver_type: string
        :param display_iter: display iterations and residual
        :type display_iter: bool
        :return: elasticity, displacement field, direct stresses (sigma xx, yy, zz), shear stresses (tau yz, xz, xy)
        :rtype: ((float, float, float, float, float, float), numpy.ndarray, numpy.ndarray, numpy.ndarray)

        :Example:
        >>> import pumapy as puma
        >>> ws = puma.Workspace.from_shape_value((20, 20, 20), 1)
        >>> ws[int(ws.matrix.shape[0] / 2):] = 2
        >>> elast_map = puma.ElasticityMap()
        >>> elast_map.add_isotropic_material((1, 1), 200, 0.3)
        >>> elast_map.add_isotropic_material((2, 2), 400, 0.1)
        >>> C, u, s, t = puma.compute_elasticity(ws, elast_map, direction='x', side_bc='f', solver_type="direct")
        Initializing and padding domains ...
    """
    if not isinstance(workspace, Workspace):
        raise Exception("Workspace must be a puma.Workspace.")
    if not isinstance(elast_map, ElasticityMap):
        raise Exception("elast_map has to be an ElasticityMap")

    solver = Elasticity(workspace, elast_map, direction, side_bc, tolerance, maxiter, solver_type, display_iter)
    solver.error_check()

    solver.log_input()
    solver.compute()
    solver.log_output()
    return solver.Ceff, solver.u, solver.s, solver.t


def get_E_nu_from_elasticity(C):
    """ Compute Young's moduli E1, E2, E3 and Poisson's ratios nu12, nu23, nu31 from symmetric elastic stiffness tensor
        :param C: 6x6 elasticity tensor
        :type C: np.ndarray
        :return: Young's moduli E1, E2, E3 and Poisson's ratios nu12, nu23, nu31
        :rtype: (float, float, float, float, float, float)
    """
    compliance = 1. / np.linalg.inv(C)
    E1 = compliance[0, 0]
    E2 = compliance[1, 1]
    E3 = compliance[2, 2]
    G23 = compliance[3, 3]
    G13 = compliance[4, 4]
    G12 = compliance[5, 5]
    nu12 = - E2 / compliance[0, 1]
    nu13 = - E3 / compliance[0, 2]
    nu23 = - E3 / compliance[1, 2]
    coeffs = [E1, E2, E3, G23, G13, G12, nu23, nu13, nu12]
    [print(i, j) for i, j in zip(["E1", "E2", "E3", "G23", "G13", "G12", "nu23", "nu13", "nu12"], coeffs)]
    return coeffs


def warp_elasticity_fields(workspace, u, s, t, scale_factor=1, show_original=False, show_cbar=True, show_edges=True):
    """ Warp the workspace according to the displacement field output by the compute_elasticity function,
        and color by displacement and stress components
        :param workspace: domain
        :type workspace: pumapy.Workspace
        :param u: displacement field as output by the compute_elasticity function
        :type u: numpy.ndarray
        :param s: direct stress field as output by the compute_elasticity function
        :type s: numpy.ndarray
        :param t: shear stress field as output by the compute_elasticity function
        :type t: numpy.ndarray
        :param scale_factor: scaling factor for warp
        :type scale_factor: float
        :param show_original: show semi-transparent original workspace before warp
        :type show_original: bool
        :param show_cbar: show colorbar in each plot
        :type show_cbar: bool
        :param show_edges: show edges in mesh
        :type show_edges: bool
    """

    if isinstance(workspace, Workspace):
        ws = workspace.matrix

    orientation = u.copy()

    x = np.linspace(0, orientation.shape[0] - 1, orientation.shape[0])
    y = np.linspace(0, orientation.shape[1] - 1, orientation.shape[1])
    z = np.linspace(0, orientation.shape[2] - 1, orientation.shape[2])
    x, y, z = np.meshgrid(x, y, z, indexing='ij')
    grid = pv.StructuredGrid(x, y, z)

    tmp = np.zeros((orientation[:, :, :, 0].size, 3), dtype=float)
    for i in [0, 1, 2]:
        tmp[:, i] = orientation[:, :, :, i].ravel(order='F')

    grid['vectors'] = tmp
    grid['ux'] = u[:, :, :, 0].copy().astype(float).ravel(order='F')
    grid['uy'] = u[:, :, :, 1].copy().astype(float).ravel(order='F')
    grid['uz'] = u[:, :, :, 2].copy().astype(float).ravel(order='F')
    grid['sx'] = s[:, :, :, 0].copy().astype(float).ravel(order='F')
    grid['sy'] = s[:, :, :, 1].copy().astype(float).ravel(order='F')
    grid['sz'] = s[:, :, :, 2].copy().astype(float).ravel(order='F')
    grid['tx'] = t[:, :, :, 0].copy().astype(float).ravel(order='F')
    grid['ty'] = t[:, :, :, 1].copy().astype(float).ravel(order='F')
    grid['tz'] = t[:, :, :, 2].copy().astype(float).ravel(order='F')

    f = grid.warp_by_vector('vectors', factor=scale_factor)

    p = pv.Plotter(shape=(3, 3))

    plots = [['ux', 'uy', 'uz'], ['sx', 'sy', 'sz'], ['tx', 'ty', 'tz']]
    for i in range(3):
        for j in range(3):
            p.subplot(i, j)
            p.add_mesh(f.copy(), scalars=plots[i][j], interpolate_before_map=False, show_edges=show_edges,
                       cmap='jet', show_scalar_bar=False, opacity=1)

            if show_cbar:
                p.add_scalar_bar(plots[i][j], interactive=False, vertical=True, color=(0, 0, 0), height=0.8)

            if show_original:
                grid2 = pv.UniformGrid()
                grid2.origin = (0.5, 0.5, 0.5)
                grid2.dimensions = np.array(ws.shape) + 1
                grid2["values"] = ws.flatten(order="F")
                f2 = grid2.threshold((0, ws.max()))
                p.add_mesh(f2, opacity=0.25, cmap='jet')

            p.show_bounds(grid='front', location='outer', all_edges=True, color=(0, 0, 0))
            p.background_color = (1, 1, 1)
            p.add_axes(line_width=5, color=(0, 0, 0))
    p.show()
