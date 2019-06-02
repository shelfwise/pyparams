from pyparams import PyParam

param1: int = PyParam(value=1, dtype=int, scope="loop", desc="summation start index")
param2: int = PyParam(2, int, "loop", "max number of iterations")
param3: int = PyParam(3, scope="loop")
param4: int = PyParam(value=4, dtype=int, scope="loop")
param5: int = PyParam(
    5,
    dtype=int,
    scope="loop",
    desc="'Note: some very long description, which should break line in "
         "the yaml file: `f1_score`: `0.333`'")
param6: int = PyParam(
    6,
    int,
    scope="loop",
    desc="some very long description, which should "
    "break line in the yaml file: Is it long enough?",
)
