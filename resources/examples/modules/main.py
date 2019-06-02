from pyparams import *

# @import_pyparams_as_module("model")
import test_model as model_module

# @import_pyparams_as_module("optimizer")
import adam as optimizer


trainer = ModelTrainer(
    dataset=PyParam("{{REQUIRED}}", scope="trainer/dataset"),
    model=model_module.get(),
    optimizer=optimizer.get(),
)

trainer.train()
trainer.evaluate()
