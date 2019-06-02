from pathlib import Path
from .pyparam_fn import IncludeModule, DeriveModule, PyParam, Module, IncludeSource, ReplaceModule
import os

_dir_path = Path(os.path.dirname(os.path.realpath(__file__)))


def get_project_root_path() -> Path:
    """Returns project root dir"""
    return _dir_path.parent

