from pyparams import *

gpu_devices: List[int] = PyParam(
    [0, 1, 2, 4],
    scope="global",
    desc="a list of GPU devices e.g. [0, 1]"
)

model = SomeModel(
    num_layers=PyParam(3,
                       scope="model",
                       desc="number of layers"),
    activation=PyParam("relu",
                       scope="model",
                       desc="[relu|elu|selu]"),
)

dataset = data_loader(
    dataset_path=PyParam("{{REQUIRED}}", scope="data")
)

trainer = Trainer(
    model=model,
    dataset=dataset,
    optimizer=PyParam("adam", scope="train"),
    num_train_epochs=PyParam(100, scope="train"),
    num_eval_steps=PyParam(100, scope="train"),
    gpu_devices=gpu_devices,
)

trainer.train()
