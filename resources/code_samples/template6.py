from pyparams import PyParam

foo1_dict: dict = PyParam(
    dtype=dict, value={"a": 1, "b": 2}, scope="model", desc="foo1"
)

foo2_dict: dict = PyParam(
    dtype=dict, value={"a": [1, 1, 2]}, scope="model", desc="foo2"
)


foo3_dict: dict = PyParam(
    dtype=dict,
    value={"a": {"aa": 3, "ab": [1, 3]}, "b": [1, 2, 3], "c": "test"},
    scope="model",
    desc="foo2",
)

foo4_dict: dict = PyParam(
    dtype=list,
    value=[
        {"a": {"aa": 3, "ab": [1, 3]}, "b": [1, 2, 3], "c": "test"},
        {"A": {"AA": 15., "AB": [1]}, "B": [2, 3], "C": "TEST"}
    ],
    scope="model",
    desc="foo4 nested dict in list",
)
