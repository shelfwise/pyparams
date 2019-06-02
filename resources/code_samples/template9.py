from dataclasses import dataclass

from pyparams import PyParam


def some_function(
        x, y,
        param2: int = PyParam(2, int, "func", "b"),
        param3: float = PyParam(3, scope="func"),
        param4: int = PyParam(value=4, dtype=int, scope="func"),
        param5=PyParam(5, dtype=int, scope="func"),
        param6=PyParam(6, int, scope="func")
) -> int:
    print("test")
    return param5


result = some_function(
    0, 1,
    param2=PyParam(12, int, "func_call", "b"),
    param3=PyParam(13, scope="func_call"),
)


@dataclass
class SomeClass:
    param1: int = PyParam(value=1, scope="class")
    param2 = PyParam(2, scope="class")
    param3: int = PyParam(3, scope="class")
    param4: int = PyParam(value=4, dtype=int, scope="class")
    param5: int = PyParam(5, dtype=int, scope="class")
    param6: int = PyParam(6, int, scope="class", desc="last param")

    def class_func(
            self,
            arg1: float = PyParam(value=1.1, scope="class/func/arg"),
            arg2=PyParam(value=2.2, scope="class/func/arg"),
    ) -> bool:
        return self.param1 + self.param2 + arg1 + arg2


global_param: int = PyParam(value=1, scope="class")


def nested_function(
        x, y,
        np1: int = PyParam(2, int, "np", "b"),

):
    def nested_function2(
            x, y,
            np2: int = PyParam(2, int, "np", "b"),
    ) -> bool:
        np3: int = PyParam(2, int, "np", "b")
        pass

    np4: int = PyParam(2, int, "np", "b")

    return nested_function2