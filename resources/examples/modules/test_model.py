from dataclasses import dataclass
from pyparams import *


@dataclass
class Model:
    num_layers: int = PyParam(5)
    activation: str = PyParam("relu")

    def predict(self, inputs):
        pass


def get():
    return Model()
