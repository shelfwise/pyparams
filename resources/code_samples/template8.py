from pyparams import PyParam

param1: int = PyParam(value=1, dtype=int, scope="loop", desc="a")
param2: int = PyParam(2, int, "loop", "b")
param3: int = PyParam(3, scope="loop")
param4: int = PyParam(value=4, dtype=int, scope="loop2")
param5: int = PyParam(5, dtype=int, scope="loop2")
param6: int = PyParam(6, int, scope="loop")
