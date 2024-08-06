import sys
import numpy as np


# DTYPE = float

def generate(matrix, l_x, l_y, l_z, wmin, wmax, qmin, qmax, equation):
    len_x = l_x
    len_y = l_y
    len_z = l_z
    q_min = qmin
    q_max = qmax
    w_min = wmin
    w_max = wmax
    # i, j, k = 0
    # print(len(matrix))
    # print(matrix.size)
    # print(type(matrix))

    x_ = np.linspace(0, len_x-1, len_x)
    y_ = np.linspace(0., len_y-1., len_y)
    z_ = np.linspace(0., len_z-1, len_z)

    x, y, z = np.meshgrid(x_, y_, z_, indexing='ij')
    assert np.all(x[:, 0, 0] == x_)
    assert np.all(y[0, :, 0] == y_)
    assert np.all(z[0, 0, :] == z_)

    q = q_min + z / (float(len_z) - 1) * (q_max - q_min)
    w = w_min + z / (float(len_z) - 1) * (w_max - w_min)

    # w = w_min
    # q = q_min
    # print(q)
    # print(w)

    if equation == 0 or equation == 1:
        print("did not set up ")
    elif equation == 2:
        matrix = np.cos(np.multiply(w, x)) + np.cos(np.multiply(w, y)) + np.cos(np.multiply(w, z)) + q
    elif equation == 3:
        matrix = np.multiply(np.sin(np.multiply(w, x)), np.cos(np.multiply(w, y))) + np.multiply(np.sin(np.multiply(w, y)), np.cos(np.multiply(w, z))) + np.multiply(np.sin(np.multiply(w, z)), np.cos(np.multiply(w, x))) + q
    elif equation == 4:
        print("using equation 4")
        matrix = (2 * (np.multiply(np.cos(np.multiply(w, x)), np.cos(np.multiply(w, y))) + np.multiply(np.cos(np.multiply(w, z)), np.cos(np.multiply(w, x))) + np.multiply(np.cos(np.multiply(w, y)), np.cos(np.multiply(w, z))))) - (np.cos(np.multiply(2, np.multiply(w, x))) + np.cos(np.multiply(2, np.multiply(w, y))) + np.cos(np.multiply(2, np.multiply(w, z)))) + q
    elif equation == 5:
        matrix = np.multiply(np.cos(np.multiply(w, x)), np.multiply(np.cos(np.multiply(w, y)), np.cos(np.multiply(w, z)))) - np.multiply(np.sin(np.multiply(w, x)), np.multiply(np.sin(np.multiply(w, y)), np.sin(np.multiply(w, z)))) + q
    elif equation == 6:
        matrix = 2 * (np.multiply(np.cos(np.multiply(w, x)), np.multiply(np.cos(np.multiply(w, y)), np.cos(np.multiply(w, z))))) + np.multiply(np.sin(np.multiply(2, np.multiply(w, x))), np.sin(np.multiply(w, y))) + np.multiply(np.sin(np.multiply(w, x)), np.sin(np.multiply(2, np.multiply(w, z)))) + np.multiply(np.sin(np.multiply(2, np.multiply(w, y))), np.sin(np.multiply(w, z))) + q


    # if equation == 0:
    #     print("checking test")
    #     for i in range(len_x):
    #         sys.stdout.write("\rGenerating TPMS ... {:.1f}% ".format(float(i) / (len_x-1) * 100))
    #         for j in range(len_y):
    #             for k in range(len_z):
    #                 q = q = q_min + (float(k)/(float(len_z)-1))*(q_max-q_min)
    #                 w = w = w_min + (float(k)/(float(len_z)-1))*(w_max-w_min)
    #                 matrix[i,j,k] = np.np.sin(np.multiply(np.multiply(w * i)) * np.np.sin(np.multiply(w * j) * np.np.sin(np.multiply(w * k) + np.np.sin(np.multiply(w * i) * np.cos(w * j) * np.cos(w * k) + \
    #                                 np.cos(w * i) * np.np.sin(np.multiply(w * j) * np.cos(w * k) + np.cos(w * i) * np.cos(w * j) * np.np.sin(np.multiply(w * k) + q
    # elif equation == 1:
    #     for i in range(len_x):
    #         sys.stdout.write("\rGenerating TPMS ... {:.1f}% ".format(float(i) / (len_x-1) * 100))
    #         for j in range(len_y):
    #             for k in range(len_z):
    #                 q = q = q_min + (float(k)/(float(len_z)-1))*(q_max-q_min)
    #                 w = w = w_min + (float(k)/(float(len_z)-1))*(w_max-w_min)
    #                 matrix[i,j,k] = np.cos(w * i) * np.np.sin(np.multiply(w * j) + np.cos(w * j) * np.np.sin(np.multiply(w * k) + np.cos(w * k) * np.cos(w * i) + q
    # elif equation == 2:
    #     for i in range(len_x):
    #         sys.stdout.write("\rGenerating TPMS ... {:.1f}% ".format(float(i) / (len_x-1) * 100))
    #         for j in range(len_y):
    #             for k in range(len_z):
    #                 q = q = q_min + (float(k)/(float(len_z)-1))*(q_max-q_min)
    #                 w = w = w_min + (float(k)/(float(len_z)-1))*(w_max-w_min)
    #                 matrix[i,j,k] =  np.cos(w * i) + np.cos(w * j) + np.cos(w * k) + q
    # elif equation == 3:
    #     for i in range(len_x):
    #         sys.stdout.write("\rGenerating TPMS ... {:.1f}% ".format(float(i) / (len_x - 1) * 100))
    #         for j in range(len_y):
    #             for k in range(len_z):
    #                 q = q = q_min + (float(k) / (float(len_z) - 1)) * (q_max - q_min)
    #                 w = w = w_min + (float(k) / (float(len_z) - 1)) * (w_max - w_min)
    #                 matrix[i, j, k] = np.sin(np.multiply(w * i) *np.cos(np.multiply(w * j) + np.sin(np.multiply(w * j) *np.cos(np.multiply(w * k) + np.sin(np.multiply(w * k) *np.cos(np.multiply(w * i) + q

    # elif equation == 4:
    #     for i in range(len_x):
    #         sys.stdout.write("\rGenerating TPMS ... {:.1f}% ".format(float(i) / (len_x - 1) * 100))
    #         for j in range(len_y):
    #             for k in range(len_z):
    #                 q = q = q_min + (float(k) / (float(len_z) - 1)) * (q_max - q_min)
    #                 w = w = w_min + (float(k) / (float(len_z) - 1)) * (w_max - w_min)
    #                 matrix[i, j, k] = (2 * (np.cos(np.multiply(w * i) *np.cos(np.multiply(w * j) +np.cos(np.multiply(w * k) *np.cos(np.multiply(w * i) +np.cos(np.multiply(w * j) *np.cos(np.multiply(w * k))) - (
    #                                              np.cos(np.multiply(2 * w * i) *np.cos(np.multiply(2 * w * j) *np.cos(np.multiply(2 * w * k)) + q


    # elif equation == 5:
    #     for i in range(len_x):
    #         sys.stdout.write("\rGenerating TPMS ... {:.1f}% ".format(float(i) / (len_x - 1) * 100))
    #         for j in range(len_y):
    #             for k in range(len_z):
    #                 q = q = q_min + (float(k) / (float(len_z) - 1)) * (q_max - q_min)
    #                 w = w = w_min + (float(k) / (float(len_z) - 1)) * (w_max - w_min)
    #                 matrix[i, j, k] =np.cos(np.multiply(w * i) *np.cos(np.multiply(w * j) *np.cos(np.multiply(w * k) - np.sin(np.multiply(w * i) * np.sin(np.multiply(w * j) * np.sin(np.multiply(w * k) + q

    # elif equation == 6:
    #     for i in range(len_x):
    #         sys.stdout.write("\rGenerating TPMS ... {:.1f}% ".format(float(i) / (len_x - 1) * 100))
    #         for j in range(len_y):
    #             for k in range(len_z):
    #                 q = q = q_min + (float(k) / (float(len_z) - 1)) * (q_max - q_min)
    #                 w = w = w_min + (float(k) / (float(len_z) - 1)) * (w_max - w_min)
    #                 matrix[i, j, k] = 2 *np.cos(np.multiply(w * i) *np.cos(np.multiply(w * j) *np.cos(np.multiply(w * k) + np.sin(np.multiply(2 * w * i) * np.sin(np.multiply(2 * j) + np.sin(np.multiply(
    #                     w * i) * np.sin(np.multiply(2 * w * k) + np.sin(np.multiply(2 * w * i) * np.sin(np.multiply(w * k) + q

    matrix[matrix < 0.8] = 0.8
    matrix[matrix > 1.2] = 1.2

    # for i in range(len_x):
    #         for j in range(len_y):
    #             for k in range(len_z):
    #                 if matrix[i,j,k] < 0.8:
    #                     matrix[i,j,k] = 0.8
    #                 if matrix[i,j,k] > 1.2:
    #                     matrix[i,j,k] = 1.2

    return matrix