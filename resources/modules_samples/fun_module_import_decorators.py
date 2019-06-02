from pyparams import *
import numpy as np

# @import_pyparams_as_module("a")
import fun_module as matmul1
# @import_pyparams_as_module()
import fun_module as matmul2

# @import_pyparams_as_source()
from fun_module  import  *

some_param: int = PyParam(4, scope="some_param")

W = np.random.rand(10, 10)
X = np.random.rand(10, 1)
Y = matmul1.matmul(W, X)
Y = matmul2.matmul(W, Y)
