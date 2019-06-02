"""Module definition"""
import ast
import os
from pathlib import Path
from typing import List, Any, Dict

from dataclasses import dataclass

import pyparams.pyparam as pyparam
from pyparams import pyparam_parser as parser
from pyparams.pyparam_fn import IncludeModule


@dataclass(frozen=True)
class PyParamModule(pyparam.NamedBasePyParam):
    """
    PyParamModule container.

    Args:
        path: a path to the module
        scope: a scope of the whole module

    """

    path: str
    scope: str = ""

    @staticmethod
    def from_ast_node(node: ast.AnnAssign) -> "PyParamModule":
        """Converts AST node to PyParam object

        Args:
            node: an instance of AnnAssign node.

        Returns:
            pyparam: PyParam object
        """
        args, keywords = PyParamModule.parse_args_kwargs_from_node(node)
        return PyParamModule(node.target.id, *args, **keywords)

    @property
    def full_name(self) -> str:
        return os.path.join(self.path, self.name)

    @property
    def value(self) -> str:
        return "_pyparam_module__" + self.name + "()"

    @property
    def module_path(self) -> str:
        return "/".join(self.path.split(".")) + ".py"

    def module_source(self, base_path: Path) -> str:
        for folder in base_path.rglob("*"):
            path = folder.parent / Path(self.module_path)
            if path.exists():
                return parser.read_source_code(path)

        raise FileNotFoundError(
            f"Cannot find module: {self.module_path}, search path: {base_path}")

    def find_module_source(self, search_folders: List[Path]) -> str:
        sources = []
        for search_folder in search_folders:
            try:
                source = self.module_source(search_folder)
                sources.append((search_folder, source))
            except ValueError:
                pass

        if len(sources) == 0:
            folders = [str(folder) for folder in search_folders]
            raise FileNotFoundError(
                f"Cannot find module: {self.module_path} in search paths: {folders}"
            )
        elif len(sources) > 1:
            raise ValueError(
                f"Found more than one modules with path {self.module_path}"
            )
        return sources[0][1]

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError("to_dict is not implemented ...")

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "PyParamModule":
        raise NotImplementedError("from_dict is not implemented ...")

    def encapsulate_source_with_class(self, module_source: str) -> str:
        """Add class and __init__ function to the module source code.
        Additionally this function will expose all functions with
        `self.function = function` assignment. Encapsulating module
        allows us to use the same module multiple times in the code,
        but with different scope.

        Args:
            module_source: a source of some python module

        Returns:
            same source code encapsulated by class statement.
        """
        source_code_module = ast.parse(source=module_source)
        nodes = parser.find_function_def_nodes(source_code_module)
        defined_functions = [node.name for node in nodes]

        lines = module_source.split("\n")
        IND = parser.COMPILED_SOURCE_INDENTATION
        new_lines = [f"class {self.value}:", f"{IND}def __init__(self):"]
        for line in lines:
            new_lines.append(f"{IND}{IND}{line}")

        for func_name in defined_functions:
            # for simplicity generate assignments only for public functions
            if not func_name.startswith("_"):
                new_lines.append(f"{IND}{IND}self.{func_name} = {func_name}")

        return "\n".join(new_lines)

    def render_as_ast_node(self, lineno: int, col_offset: int) -> ast.AST:
        """
        Render PyParamModule to AST node. This implementation save
        PyParamModule as AST Call object, so not only value is
        generated but full `IncludeModule` will be generated in the source code.

        Args:
            lineno: a line number of the ast Node in the python file
            col_offset: column offset in that line

        Returns:
            node: an AST node as `IncludeModule(path, scope)`
        """

        value = f"{IncludeModule.__name__}(path='{self.path}', scope='{self.scope}')"
        node = ast.Module(body=value)
        node.lineno = lineno
        node.col_offset = col_offset
        return node
