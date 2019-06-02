from pyparams import PyParam
import numpy as np


def matmul(matrix: np.ndarray, x: np.ndarray) -> np.ndarray:
    """matrix multiplication with magic"""
    offset: float = PyParam(1.0, float, "matmul")
    alpha: float = PyParam(1.0, float, "matmul")
    return alpha * matrix @ x + offset
