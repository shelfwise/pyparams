from pyparams import *
from some_ml_lib import ModelTrainer

# @import_pyparams_as_module("model")
import modules.model_v1 as model_module
# @import_pyparams_as_module("optimizer")
import modules.adam as optimizer_module

trainer = ModelTrainer(
    dataset=PyParam("{{REQUIRED}}", scope="trainer/dataset"),
    model=model_module.get(),
    optimizer=optimizer_module.get(),
)

trainer.train()
trainer.evaluate()
