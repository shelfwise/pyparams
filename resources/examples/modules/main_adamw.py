from pyparams import *
DeriveModule("main")
optimizer_module: Module = ReplaceModule("modules.adamw", "optimizer")