# Template definition of model parameters
from pyparams import PyParam

version: str = PyParam(dtype=str, value="1.0", desc="model version")


base_num_filters: int = PyParam(4, scope="feature_extractor")
include_root: bool = PyParam(False, scope="feature_extractor")
regularize_depthwise: bool = PyParam(False, scope="feature_extractor")
activation_fn_in_separable_conv: bool = PyParam(False, scope="feature_extractor")
entry_flow_blocks: tuple = PyParam(
    (1, 1, 1),
    dtype=tuple,
    scope="feature_extractor",
    desc="Number of units in each bock in the entry flow.",
)
middle_flow_blocks: tuple = PyParam(
    (1,),
    dtype=tuple,
    scope="feature_extractor",
    desc="Number of units in the middle flow.",
)

X: int = 3
