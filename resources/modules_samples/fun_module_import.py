from pyparams import *
import numpy as np

matmul1: Module = IncludeModule("fun_module", scope="a")
matmul2: Module = IncludeModule("fun_module", scope="b")
some_param: int = PyParam(4, scope="some_param")

W = np.random.rand(10, 10)
X = np.random.rand(10, 1)
Y = matmul1.matmul(W, X)
Y = matmul2.matmul(W, Y)
