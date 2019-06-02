from pyparams import PyParam

start_index: int = PyParam(1, scope="loop", desc="summation start index")


def sum_numbers():
    """Sum numbers """
    s = 0
    max_iters: int = PyParam(6, int, "loop", "max number of iterations")
    for i in range(start_index, max_iters):
        s += i
    return s


print(sum_numbers())
