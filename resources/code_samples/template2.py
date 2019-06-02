from pyparams import PyParam

version: str = PyParam(dtype=str, value="1.0", desc="model version")

foo1: int = PyParam(dtype=int, value=1, scope="model", desc="foo1")

foo2: float = PyParam(dtype=float, value=2, scope="model", desc="foo2")

image_foo1: float = PyParam(dtype=float, value=2, scope="image", desc="")

image_foo2: tuple = PyParam(
    dtype=tuple, value=(64, 64), scope="image", desc="shape of the image"
)

image_foo3: tuple = PyParam(
    dtype=tuple, value=(32, 32), scope="image/shape", desc="shape of some image"
)

bar1: list = PyParam(dtype=list, value=[64, 64], scope="", desc="something")

y = foo1 + foo2
