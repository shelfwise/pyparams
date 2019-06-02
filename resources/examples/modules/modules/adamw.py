import tensorflow as tf
from pyparams import PyParam


def get() -> tf.train.Optimizer:

    lr: float = PyParam(0.01, scope="adamw")
    weight_decay: float = PyParam(value=5e-6, scope="adamw")
    beta1: float = PyParam(value=0.9, scope="adamw")
    beta2: float = PyParam(value=0.995, scope="adamw")
    epsilon: float = PyParam(value=1e-8, scope="adamw")

    optimizer = tf.contrib.opt.AdamWOptimizer(
        weight_decay=weight_decay,
        learning_rate=lr,
        beta1=beta1,
        beta2=beta2,
        epsilon=epsilon,
    )

    return optimizer