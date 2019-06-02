from pyparams import PyParam, Module, IncludeModule, IncludeSource

some_global1: float = PyParam(1.0, float, "global_const")

matmul_module: Module = IncludeModule("fun_module", scope="matmul_fun")

# this code will be included here
IncludeSource("fun_module")


def in_func():
    # this code will be included here
    IncludeSource(path="fun2_module")
    local1: float = PyParam(1.0, float, "local_const")
    local1 = 0
    x = PyParam(1.0)
    PyParam(2.0)


some_global2: float = PyParam(1.0, float, "global_const")
