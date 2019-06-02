"""
This file contain main PyParams objects which can be parsed by
PyParam library. The objects defined here are used as a code
annotations which are then parsed by pyparams functions.
"""
from typing import Optional, TypeVar

Module = TypeVar("Module")
ValueType = TypeVar("ValueType")


"""
# PyParams decorators to import and include modules with pyparams:

* #@import_pyparams_as_module(scope) - a named import used with `import as` keyword:
    Example:    
    
    # @import_pyparams_as_module("optimizer")
    import modules.optimizers.adam as optimizer_module
    
    This is exactly the same as:
    optimizer_module: Module = IncludeModule("modules.optimizers.adam", "optimizer")
"""
IMPORT_MODULE_DECORATOR = "@import_pyparams_as_module"

"""
* # @import_pyparams_as_source() - a brute-force source include, which 
    works like `#include` declaration in C/C++ languages. For example:

    Example:
    # @import_pyparams_as_source()
    from models.detection.base_templates.base_functions import *
    
    This is exactly the same as:
    IncludeSource("models.detection.base_templates.base_functions")

"""

IMPORT_SOURCE_DECORATOR = "@import_pyparams_as_source"


def PyParam(
    value: ValueType,
    dtype: Optional[type] = None,
    scope: Optional[str] = "",
    desc: Optional[str] = "",
) -> ValueType:
    """A mock implementation of the PyParam class to be used in template python files.
    Note, that it just returns value parameter. Example usage:

        num_layers: int = PyParam(10, desc="number of layers", scope="general")
        use_batchnorm: bool = PyParam(True, scope="general")
        activation_type: str = PyParam("relu")

    Args:
        value: a value to be passed
        dtype: type annotation fo the value
        scope: optional string scope of the variable
        desc: optional description of the field. This description will be rendered
            in YAML config files as a field comment.

    Returns:
        input value
    """
    return value


def IncludeModule(path: str, scope: str = "") -> Module:
    """Include module annotation. One can import same module multiple times
    however the scope parameter should be different for them. Example:

        matmul1: Module = IncludeModule("fun_module", scope="a")
        matmul2: Module = IncludeModule("fun_module", scope="b")
        optimizer_module: Module = IncludeModule("modules.optimizers.adam", "optimizer")
        backbone_module: Module = IncludeModule("modules.backbones.resnet_v1")

    Args:
        path: a path of the module
        scope: and variable scope

    Returns:
        a Module placeholder
    """
    return Module


def IncludeSource(path: str) -> None:
    """Include full source code to the current file at current place of the code.
    Source can be included in some function.

    IncludeSource("path.to.fun_module")
    def in_func():
        # this code will be included here
        IncludeSource(path="path.to.fun2_module")

    Args:
        path:

    Returns:

    """
    pass


def DeriveModule(path: str) -> Module:
    """Derive module annotation. This annotation can be used only once in the
    code!! Example module derivation:

        from pyparams import *
        DeriveModule("models/detection/SSD/model")
        backbone_module: Module = ReplaceModule("modules.backbones.inceptionV1")
        optimizer_module: Module = ReplaceModule("modules.optimizers.adamw", "optimizer")
        augmentation_module: Module = ReplaceModule("modules.augmentation.identity")

    Args:
        path: a path to module to be derived

    Returns:
        a Module placeholder
    """
    return Module


def ReplaceModule(path: str, scope: str = "") -> Module:
    """Replace module annotation which is used to derive module content. ReplaceModule
    can be used only with DeriveModule annotation.

    Example:

        backbone_module: Module = ReplaceModule("modules.backbones.inceptionV1")
        optimizer_module: Module = ReplaceModule("modules.optimizers.adamw", "optimizer")

    Args:
        path: a path to the module which should be used as a replacement
        scope: optional scope of the new module

    Returns:
        a Module placeholder
    """
    return Module




