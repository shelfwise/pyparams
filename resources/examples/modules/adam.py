import tensorflow as tf
from pyparams import PyParam


def get() -> tf.train.Optimizer:
    lr: float = PyParam(value=0.01, scope="adam")
    beta1: float = PyParam(value=0.9, scope="adam")
    beta2: float = PyParam(value=0.995, scope="adam")
    epsilon: float = PyParam(value=1e-8, scope="adam")

    optimizer = tf.train.AdamOptimizer(
        learning_rate=lr, beta1=beta1, beta2=beta2, epsilon=epsilon
    )

    return optimizer
