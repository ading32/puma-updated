from pumapy.utilities.timer import Timer
from pumapy.physicsmodels.linear_solvers import PropertySolver
from pumapy.utilities.generic_checks import estimate_max_memory
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import LinearOperator
import numpy as np


class ElasticityFE(PropertySolver):

    def __init__(self, workspace, elast_map, direction, tolerance, maxiter, solver_type, display_iter, matrix_free):

        allowed_solvers = ['minres', 'direct', 'bicgstab', 'gmres']
        super().__init__(workspace, solver_type, allowed_solvers, tolerance, maxiter, display_iter)

        self.elast_map = elast_map
        self.matrix_free = matrix_free
        self.direction = direction
        self.voxlength = self.ws.voxel_length
        self.len_x, self.len_y, self.len_z = self.ws.matrix.shape
        self.mat_elast = dict()
        self.need_to_orient = False  # changes if (E_axial, E_radial, nu_poissrat_12, nu_poissrat_23, G12) detected

        if self.direction == 'x':
            self.axis = 0
        elif self.direction == 'y':
            self.axis = 1
        elif self.direction == 'z':
            self.axis = 2
        elif self.direction == 'xy':
            self.axis = 3
        elif self.direction == 'xz':
            self.axis = 4
        else:
            self.axis = 5

        self.Ceff = None
        self.u = None
        self.s = None
        self.t = None

    def compute(self):
        t = Timer()
        estimate_max_memory("elasticity_fe", self.ws.matrix.shape, self.solver_type, self.need_to_orient, mf=self.matrix_free)
        self.initialize()
        self.compute_rhs()
        self.assemble_Amatrix()
        print("Time to assemble matrices: ", t.elapsed()); t.reset()
        super().solve()
        print("Time to solve: ", t.elapsed())
        self.compute_effective_coefficient()
        self.solve_time = t.elapsed()

    def initialize(self):
        print("Initializing indexing matrices ... ", flush=True, end='')
        self.nElems = self.len_x * self.len_y * self.len_z
        self.nDOFs = self.nElems * 3
        self.pElemDOFNum = np.zeros((24, self.nElems), dtype=np.uint32)
        self.nElemS = self.len_x * self.len_y
        nNodeS = (self.len_x + 1) * (self.len_y + 1)
        DOFMap = np.zeros((self.len_x + 1) * (self.len_y + 1) * (self.len_z + 1), dtype=int)

        # Segmenting domain according to elast_map
        for i in range(self.elast_map.get_size()):
            low, high, _ = self.elast_map.get_material(i)
            self.ws[np.logical_and(self.ws.matrix >= low, self.ws.matrix <= high)] = low

        self.elemMatMap = np.zeros(self.nElems, dtype=int)
        for k in range(self.len_z):
            for i in range(self.len_y):
                for j in range(self.len_x):
                    self.elemMatMap[i + j * self.len_y + k * self.len_x * self.len_y] = self.ws[j, i, k]

        if self.need_to_orient:
            self.elemMatMap_orient = np.zeros((self.nElems, 3), dtype=int)
            for k in range(self.len_z):
                for i in range(self.len_y):
                    for j in range(self.len_x):
                        self.elemMatMap_orient[i + j * self.len_y + k * self.len_x * self.len_y] = self.ws.orientation[j, i, k]

        # compute self.m_K and self.m_B
        self.create_element_stiffness_matrices(onlyB=False)

        for n in range(nNodeS * (self.len_z + 1)):
            i = n % nNodeS
            DOFMap[n] = (i - (i // (self.len_y + 1)) - self.len_y * ((i % (self.len_y + 1)) // self.len_y)) \
                        % self.nElemS + ((n // nNodeS) % self.len_z) * self.nElemS + 1

        for e in range(self.nElems):
            N1 = 2 + e % self.nElemS + (e % self.nElemS) // self.len_y + e // self.nElemS * nNodeS - 1
            N3 = N1 + self.len_y
            N2 = N3 + 1
            N4 = N1 - 1
            N5 = N1 + nNodeS
            N6 = N2 + nNodeS
            N7 = N3 + nNodeS
            N8 = N4 + nNodeS
            self.pElemDOFNum[0, e] = DOFMap[N1] * 3 - 3
            self.pElemDOFNum[1, e] = DOFMap[N1] * 3 - 2
            self.pElemDOFNum[2, e] = DOFMap[N1] * 3 - 1
            self.pElemDOFNum[3, e] = DOFMap[N2] * 3 - 3
            self.pElemDOFNum[4, e] = DOFMap[N2] * 3 - 2
            self.pElemDOFNum[5, e] = DOFMap[N2] * 3 - 1
            self.pElemDOFNum[6, e] = DOFMap[N3] * 3 - 3
            self.pElemDOFNum[7, e] = DOFMap[N3] * 3 - 2
            self.pElemDOFNum[8, e] = DOFMap[N3] * 3 - 1
            self.pElemDOFNum[9, e] = DOFMap[N4] * 3 - 3
            self.pElemDOFNum[10, e] = DOFMap[N4] * 3 - 2
            self.pElemDOFNum[11, e] = DOFMap[N4] * 3 - 1
            self.pElemDOFNum[12, e] = DOFMap[N5] * 3 - 3
            self.pElemDOFNum[13, e] = DOFMap[N5] * 3 - 2
            self.pElemDOFNum[14, e] = DOFMap[N5] * 3 - 1
            self.pElemDOFNum[15, e] = DOFMap[N6] * 3 - 3
            self.pElemDOFNum[16, e] = DOFMap[N6] * 3 - 2
            self.pElemDOFNum[17, e] = DOFMap[N6] * 3 - 1
            self.pElemDOFNum[18, e] = DOFMap[N7] * 3 - 3
            self.pElemDOFNum[19, e] = DOFMap[N7] * 3 - 2
            self.pElemDOFNum[20, e] = DOFMap[N7] * 3 - 1
            self.pElemDOFNum[21, e] = DOFMap[N8] * 3 - 3
            self.pElemDOFNum[22, e] = DOFMap[N8] * 3 - 2
            self.pElemDOFNum[23, e] = DOFMap[N8] * 3 - 1
        print("Done")

    def compute_rhs(self):
        print("Creating b vector ... ", flush=True, end='')
        self.bvec = np.zeros(self.nDOFs, dtype=float)

        if not self.need_to_orient:
            for e in range(self.nElems):
                np.add.at(self.bvec, self.pElemDOFNum[:, e], self.m_B[self.axis, :, self.elemMatMap[e]])
        else:
            for e in range(self.nElems):
                np.add.at(self.bvec, self.pElemDOFNum[:, e], self.m_B[self.axis, :, e])
        del self.m_B
        print("Done")

    def assemble_Amatrix(self):
        print("Creating A matrix ... ", flush=True, end='')
        y = np.zeros(self.nDOFs, dtype=float)

        if self.matrix_free and self.solver_type != 'direct' and not self.need_to_orient:
            def matvec(x):  # overload matvec for Amat=LinearOperator - only for isotropic phases
                y.fill(0)
                np.add.at(y, self.pElemDOFNum, np.einsum("ijk, jk -> ik", self.m_K[:, :, self.elemMatMap], x[self.pElemDOFNum]))
                return y
            self.Amat = LinearOperator(shape=(self.nDOFs, self.nDOFs), matvec=matvec)

        else:  # actually assemble sparse matrix
            range24 = np.arange(24)
            m_K_inds = (np.tile(range24, 24), np.repeat(range24, 24))
            I, J = np.zeros((2, self.nElems * 576), dtype=np.uint32)
            V = np.zeros(self.nElems * 576, dtype=float)
            counter = 0
            if self.need_to_orient:
                for e in range(self.nElems):
                    I[counter:counter + 576] = np.repeat(self.pElemDOFNum[range24, e], 24)
                    J[counter:counter + 576] = np.tile(self.pElemDOFNum[range24, e], 24)
                    V[counter:counter + 576] = self.m_K[m_K_inds[0], m_K_inds[1], e]
                    counter += 576
            else:
                for e in range(self.nElems):
                    I[counter:counter + 576] = np.repeat(self.pElemDOFNum[range24, e], 24)
                    J[counter:counter + 576] = np.tile(self.pElemDOFNum[range24, e], 24)
                    V[counter:counter + 576] = self.m_K[m_K_inds[0], m_K_inds[1], self.elemMatMap[e]]
                    counter += 576
            del self.m_K
            self.Amat = coo_matrix((V, (I, J))).tocsc()

        print("Done")

    def compute_effective_coefficient(self):
        print("Computing stresses ... ", flush=True, end='')

        if self.matrix_free and self.solver_type != 'direct' and not self.need_to_orient:
            del self.m_K

        # compute self.m_B
        self.create_element_stiffness_matrices(onlyB=True)

        self.u = np.zeros((self.len_x, self.len_y, self.len_z, 3))
        for k in range(self.len_z):
            for i in range(self.len_y):
                for j in range(self.len_x):
                    self.u[j, i, k, 0] = self.x[(i + j * self.len_y + k * self.len_x * self.len_y) * 3 - 3]
                    self.u[j, i, k, 1] = self.x[(i + j * self.len_y + k * self.len_x * self.len_y) * 3 - 2]
                    self.u[j, i, k, 2] = self.x[(i + j * self.len_y + k * self.len_x * self.len_y) * 3 - 1]

        t = np.zeros(24, dtype=float)
        if self.axis == 0:
            t[[3, 6, 15, 18]] = 1
        elif self.axis == 1:
            t[[7, 10, 19, 22]] = 1
        elif self.axis == 2:
            t[[14, 17, 20, 23]] = 1
        elif self.axis == 3:
            t[[6, 9, 18, 21]] = 1
        elif self.axis == 4:
            t[[12, 15, 18, 21]] = 1
        elif self.axis == 5:
            t[[8, 11, 20, 23]] = 1

        s_f = np.zeros((self.nElems, 3), dtype=float)
        t_f = np.zeros((self.nElems, 3), dtype=float)
        if not self.need_to_orient:
            for e in range(self.nElems):
                s_f[e, 0] += (self.m_B[0, :, self.elemMatMap[e]] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                s_f[e, 1] += (self.m_B[1, :, self.elemMatMap[e]] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                s_f[e, 2] += (self.m_B[2, :, self.elemMatMap[e]] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                t_f[e, 2] += (self.m_B[3, :, self.elemMatMap[e]] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                t_f[e, 1] += (self.m_B[4, :, self.elemMatMap[e]] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                t_f[e, 0] += (self.m_B[5, :, self.elemMatMap[e]] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
        else:
            for e in range(self.nElems):
                s_f[e, 0] += (self.m_B[0, :, e] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                s_f[e, 1] += (self.m_B[1, :, e] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                s_f[e, 2] += (self.m_B[2, :, e] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                t_f[e, 2] += (self.m_B[3, :, e] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                t_f[e, 1] += (self.m_B[4, :, e] * (t - self.x[self.pElemDOFNum[:, e]])).sum()
                t_f[e, 0] += (self.m_B[5, :, e] * (t - self.x[self.pElemDOFNum[:, e]])).sum()

        self.s = np.zeros((self.len_x, self.len_y, self.len_z, 3))
        self.t = np.zeros((self.len_x, self.len_y, self.len_z, 3))
        for k in range(self.len_z):
            for i in range(self.len_y):
                for j in range(self.len_x):
                    self.s[j, i, k, 0] = s_f[i + j * self.len_y + k * self.len_x * self.len_y, 0]
                    self.s[j, i, k, 1] = s_f[i + j * self.len_y + k * self.len_x * self.len_y, 1]
                    self.s[j, i, k, 2] = s_f[i + j * self.len_y + k * self.len_x * self.len_y, 2]
                    self.t[j, i, k, 0] = t_f[i + j * self.len_y + k * self.len_x * self.len_y, 0]
                    self.t[j, i, k, 1] = t_f[i + j * self.len_y + k * self.len_x * self.len_y, 1]
                    self.t[j, i, k, 2] = t_f[i + j * self.len_y + k * self.len_x * self.len_y, 2]

        self.Ceff = [self.s[:, :, :, 0].sum() / self.nElems, self.s[:, :, :, 1].sum() / self.nElems, self.s[:, :, :, 2].sum() / self.nElems,
                     self.t[:, :, :, 0].sum() / self.nElems, self.t[:, :, :, 1].sum() / self.nElems, self.t[:, :, :, 2].sum() / self.nElems]
        print("Done")

    def create_element_stiffness_matrices(self, onlyB):

        if self.need_to_orient:
            if not onlyB:
                self.m_K = np.zeros((24, 24, self.nElems), dtype=float)
            self.m_B = np.zeros((6, 24, self.nElems), dtype=float)
        else:
            nMat = len(self.mat_elast)
            if not onlyB:
                self.m_K = np.zeros((24, 24, nMat), dtype=float)
            self.m_B = np.zeros((6, 24, nMat), dtype=float)

        k = np.zeros((24, 24), dtype=float)
        BC = np.zeros((6, 24), dtype=float)
        B = np.zeros((6, 24), dtype=float)
        C = np.zeros((6, 6), dtype=float)
        B_inds = [[0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5, 3, 4, 5], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 23]]
        dNdx_inds = [[0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 1, 2, 2, 0, 0, 1, 1, 2, 2, 0, 0, 1, 1, 2, 2, 0, 0, 1, 1, 2, 2, 0, 0, 1, 1, 2, 2, 0, 0, 1, 1, 2, 2, 0, 0, 1, 1, 2, 2, 0, 0, 1, 1, 2, 2, 0, 0, 1], [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 7, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7]]

        # Gauss Points
        gp = [-1. / np.sqrt(3), 1. / np.sqrt(3)]

        # Element coords
        x = np.array([0., 1., 1., 0., 0., 1., 1., 0.])
        y = np.array([0., 0., 1., 1., 0., 0., 1., 1.])
        z = np.array([0., 0., 0., 0., 1., 1., 1., 1.])

        if self.need_to_orient:
            KBiso_prev = dict()
            for e in range(self.nElems):
                cs = self.mat_elast[self.elemMatMap[e]]

                if len(cs) == 21:
                    if self.elemMatMap[e] in KBiso_prev.keys():
                        if onlyB:
                            self.m_B[:, :, e] = KBiso_prev[self.elemMatMap[e]]
                        else:
                            self.m_K[:, :, e], self.m_B[:, :, e] = KBiso_prev[self.elemMatMap[e]]
                        continue
                    C[:] = self.create_C(cs)
                else:
                    C[:] = self.orient_C(cs, e)

                self.compute_element_stiffness(C, k, BC, B, gp, x, y, z, B_inds, dNdx_inds, e, onlyB)

                if len(cs) == 21:  # store previously computed k,BC for isotropic phases
                    if onlyB:
                        KBiso_prev[self.elemMatMap[e]] = self.m_B[:, :, e]
                    else:
                        KBiso_prev[self.elemMatMap[e]] = self.m_K[:, :, e], self.m_B[:, :, e]
        else:
            i_mat = 0
            for j_mat in range(0, 256):

                if j_mat not in self.mat_elast.keys():
                    continue

                C[:] = self.create_C(self.mat_elast[j_mat])
                self.compute_element_stiffness(C, k, BC, B, gp, x, y, z, B_inds, dNdx_inds, i_mat, onlyB)
                i_mat += 1

    def create_C(self, cs):
        return np.array([[cs[0], cs[1], cs[2], cs[3], cs[4], cs[5]],
                         [cs[1], cs[6], cs[7], cs[8], cs[9], cs[10]],
                         [cs[2], cs[7], cs[11], cs[12], cs[13], cs[14]],
                         [cs[3], cs[8], cs[12], cs[15], cs[16], cs[17]],
                         [cs[4], cs[9], cs[13], cs[16], cs[18], cs[19]],
                         [cs[5], cs[10], cs[14], cs[17], cs[19], cs[20]]])

    def orient_C(self, cs, e):
        E1, E2, v12, v23, G12 = cs
        v21 = v12 * E2 / E1
        delta = 1 - 2 * v12 * v21 - v23 * v23 - 2 * v21 * v12 * v23
        C_init = np.array([[((1 - v23 * v23) * E1) / delta, (v21 * (1 + v23) * E1) / delta, (v21 * (1 + v23) * E1) / delta, 0, 0, 0],
                           [(v21 * (1 + v23) * E1) / delta, ((1 - v12 * v21) * E2) / delta, ((v23 + v21 * v12) * E2) / delta, 0, 0, 0],
                           [(v21 * (1 + v23) * E1) / delta, ((v23 + v21 * v12) * E2) / delta, ((1 - v21 * v12) * E2) / delta, 0, 0, 0],
                           [0, 0, 0, ((1 - v23 - 2 * v21 * v12) * E2) / delta, 0, 0],
                           [0, 0, 0, 0, 2 * G12, 0],
                           [0, 0, 0, 0, 0, 2 * G12]])

        # Rotation matrix
        theta = np.arctan2(self.elemMatMap_orient[e, 1], self.elemMatMap_orient[e, 0])
        a21 = -np.sin(theta)
        a22 = np.cos(theta)
        beta = np.arcsin(self.elemMatMap_orient[e, 2])
        a13 = np.sin(beta)
        a33 = np.cos(beta)
        a11 = a22 * a33
        a12 = - a21 * a33
        a31 = - a22 * a13
        a32 = a21 * a13
        a23 = 0
        R = np.array([[a11 ** 2, a12 ** 2, a13 ** 2, a12 * a13, a11 * a13, a11 * a12],
                      [a21 ** 2, a22 ** 2, a23, a23, a23, a21 * a22],
                      [a31 ** 2, a32 ** 2, a33 ** 2, a32 * a33, a33 * a31, a31 * a32],
                      [2 * a21 * a31, 2 * a32 * a22, a23, a22 * a33, a21 * a33, a21 * a32 + a22 * a31],
                      [2 * a11 * a31, 2 * a12 * a32, 2 * a13 * a33, a32 * a13 + a33 * a12, a11 * a33 + a13 * a31, a31 * a12 + a32 * a11],
                      [2 * a11 * a21, 2 * a12 * a22, a23, a13 * a22, a13 * a21, a11 * a22 + a12 * a21]])
        return R.T @ C_init @ R.T

    def compute_element_stiffness(self, C, k, BC, B, gp, x, y, z, B_inds, dNdx_inds, KBind, onlyB):
        if not onlyB:
            k.fill(0)
        BC.fill(0)
        B.fill(0)
        for i in range(2):
            r = gp[i]
            for j in range(2):
                s = gp[j]
                for l in range(2):
                    t = gp[l]

                    X = np.array([x.T, y.T, z.T])

                    # Compute B matrix and Jacobian
                    dN1dr = -(1 - s) * (1 - t) * .125
                    dN2dr = (1 - s) * (1 - t) * .125
                    dN3dr = (1 + s) * (1 - t) * .125
                    dN4dr = -(1 + s) * (1 - t) * .125
                    dN5dr = -(1 - s) * (1 + t) * .125
                    dN6dr = (1 - s) * (1 + t) * .125
                    dN7dr = (1 + s) * (1 + t) * .125
                    dN8dr = -(1 + s) * (1 + t) * .125
                    dN1ds = -(1 - r) * (1 - t) * .125
                    dN2ds = -(1 + r) * (1 - t) * .125
                    dN3ds = (1 + r) * (1 - t) * .125
                    dN4ds = (1 - r) * (1 - t) * .125
                    dN5ds = -(1 - r) * (1 + t) * .125
                    dN6ds = -(1 + r) * (1 + t) * .125
                    dN7ds = (1 + r) * (1 + t) * .125
                    dN8ds = (1 - r) * (1 + t) * .125
                    dN1dt = -(1 - r) * (1 - s) * .125
                    dN2dt = -(1 + r) * (1 - s) * .125
                    dN3dt = -(1 + r) * (1 + s) * .125
                    dN4dt = -(1 - r) * (1 + s) * .125
                    dN5dt = (1 - r) * (1 - s) * .125
                    dN6dt = (1 + r) * (1 - s) * .125
                    dN7dt = (1 + r) * (1 + s) * .125
                    dN8dt = (1 - r) * (1 + s) * .125
                    dN = np.array([[dN1dr, dN2dr, dN3dr, dN4dr, dN5dr, dN6dr, dN7dr, dN8dr],
                                   [dN1ds, dN2ds, dN3ds, dN4ds, dN5ds, dN6ds, dN7ds, dN8ds],
                                   [dN1dt, dN2dt, dN3dt, dN4dt, dN5dt, dN6dt, dN7dt, dN8dt]])
                    J = dN @ X.T
                    dNdx = np.linalg.inv(J) @ dN

                    for ind in range(len(B_inds[0])):
                        B[B_inds[0][ind], B_inds[1][ind]] = dNdx[dNdx_inds[0][ind], dNdx_inds[1][ind]]

                    detJ = np.linalg.det(J)
                    if not onlyB:
                        k += (B.T @ C @ B) * detJ
                    BC += (C @ B) * detJ

        if not onlyB:
            self.m_K[:, :, KBind] = k
        self.m_B[:, :, KBind] = BC

    def log_input(self):
        self.ws.log.log_section("Computing Elasticity")
        self.ws.log.log_line("Simulation direction: " + str(self.direction))
        self.ws.log.log_line("Domain Size: " + str(self.ws.get_shape()))
        self.ws.log.log_line("Elasticity Map: ")
        for i in range(self.elast_map.get_size()):
            low, high, cond = self.elast_map.get_material(i)
            self.ws.log.log_line("  - Material " + str(i) + "[" + str(low) + "," + str(high) + "," + str(cond) + "]")
        self.ws.log.log_line("Solver Type: " + str(self.solver_type))
        self.ws.log.log_line("Solver Tolerance: " + str(self.tolerance))
        self.ws.log.log_line("Max Iterations: " + str(self.maxiter))
        self.ws.log.write_log()

    def log_output(self):
        self.ws.log.log_section("Finished Elasticity Calculation")
        self.ws.log.log_line("Elasticity: " + "[" + str(self.Ceff) + "]")
        self.ws.log.log_line("Solver Time: " + str(self.solve_time))
        self.ws.log.write_log()

    def error_check(self):
        # elast_map checks
        ws_tmp_tocheck = self.ws.matrix.copy()
        for i in range(self.elast_map.get_size()):
            low, high, C = self.elast_map.get_material(i)
            self.mat_elast[low] = np.array(C)
            if len(C) == 5:
                self.need_to_orient = True
                if self.ws.orientation.shape[:3] != self.ws.matrix.shape or \
                        not 0.9 < np.min(np.linalg.norm(self.ws.orientation[np.logical_and(self.ws.matrix >= low,
                                                                                           self.ws.matrix <= high)],
                                                        axis=1)) < 1.1:
                    raise Exception("The Workspace needs an orientation in order to align the elasticity.")

            # segmenting tmp domain to check if all values covered by mat_elast
            ws_tmp_tocheck[np.logical_and(self.ws.matrix >= low, self.ws.matrix <= high)] = low

        unique_matrixvalues = np.unique(ws_tmp_tocheck)
        if (unique_matrixvalues.size != len(self.mat_elast.keys()) or
                np.all(np.sort(list(self.mat_elast.keys())).astype(np.uint16) != unique_matrixvalues)):
            raise Exception("All values in workspace must match the IDs in ElasticityMap.")

        # direction checks
        if self.direction.lower() in ['x', 'y', 'z', 'yz', 'xz', 'xy']:
            self.direction = self.direction.lower()
        else:
            raise Exception("Invalid simulation direction, it can only be 'x', 'y', 'z', 'yz', 'xz', 'xy'.")
