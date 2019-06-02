from pyparams import PyParam
import numpy as np


def matmul(matrix: np.ndarray, x: np.ndarray):
    """matrix multiplication with magic"""
    bias: float = PyParam(1.1, float, "matmul")
    beta: float = PyParam(1.2, float, "matmul")
    return beta * matrix @ x + bias
