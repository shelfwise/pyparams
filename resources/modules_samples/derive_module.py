# This code will take the code from fun_module_import.py
# and replace matmul2 variable with fun2_module definition
from pyparams import *

DeriveModule("fun_module_import")
matmul2: Module = ReplaceModule("fun2_module", scope="c")
