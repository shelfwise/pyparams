import ast
import os
from abc import abstractmethod
from typing import Any, Optional, Dict, Union

import dataclasses as dc

# A mapping used when reading dtype from yml files.
_str_to_dtype = {
    "int": int,
    "str": str,
    "float": float,
    "tuple": tuple,
    "list": list,
    "dict": dict,
    "set": set,
    "bool": bool,
}

_dtype_to_str = {v: k for k, v in _str_to_dtype.items()}


def ast_node_to_value(node: ast.AST) -> Any:
    """
    Returns a python variable of dtype which depends on the input AST node.
    For example if type(node) == ast.Name this function will extract string
    value stored in id parameter.
    Note: not all nodes are supported.

    Args:
        node: an AST node extracted from parsed python file

    Returns:
        value: a node value. This can be a scalar int, string or even nested structures
            like dicts etc.

    Raises:
        ValueError: when the type of the node is not supported
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Tuple):
        return [ast_node_to_value(e) for e in node.elts]
    elif isinstance(node, ast.List):
        return [ast_node_to_value(e) for e in node.elts]
    elif isinstance(node, ast.NameConstant):
        return node.value
    elif isinstance(node, ast.Attribute):
        if isinstance(node, ast.Attribute):
            return ast_node_to_value(node.value) + "." + node.attr
        else:
            return node.value.id + "." + node.attr
    elif isinstance(node, ast.Subscript):
        return ast_node_to_value(node.value)
    elif isinstance(node, str):
        return node
    elif isinstance(node, ast.keyword):
        return ast_node_to_value(node.arg), ast_node_to_value(node.value)
    elif isinstance(node, ast.Call):
        data = {
            "name": ast_node_to_value(node.func),
            "args": [ast_node_to_value(arg) for arg in node.args],
            "keywords": [ast_node_to_value(arg) for arg in node.keywords],
        }
        return data
    elif isinstance(node, ast.Dict):
        return {
            ast_node_to_value(key): ast_node_to_value(value)
            for key, value in zip(node.keys, node.values)
        }
    else:
        raise ValueError(
            f"Cannot parse AST node of type: {type(node)}. "
            f"Node parameters: {node.__dict__}"
        )


def value_to_ast_node(value: Any, dtype: type) -> ast.AST:
    """An inverse operation to @ast_node_to_value function. This function takes
    some value (str, int, or nested structures of dicts list etc) and return
    corresponding AST node.

    For example: value=5, dtype=int, this function will return: ast.Num(value)

    Args:
        value: a python variable like: 4, 'text', {'s': 5, 't': [1, 2]}
        dtype: a python type of the value which determines the output type
            of the AST node.

    Returns:
        node: initialized AST node

    Raises:
        ValueError: when the dtype of is not supported
    """

    if dtype in [int, float]:
        return ast.Num(value)
    elif dtype == bool:
        return ast.NameConstant(value)
    elif dtype == str:
        return ast.Str(value)
    elif dtype == list:
        return ast.List(elts=[value_to_ast_node(e, type(e)) for e in value])
    elif dtype == tuple:
        return ast.Tuple(elts=[value_to_ast_node(e, type(e)) for e in value])
    elif dtype == dict:
        return ast.Dict(
            keys=[value_to_ast_node(key, type(key)) for key in value.keys()],
            values=[value_to_ast_node(val, type(val)) for val in value.values()],
        )
    elif dtype == type:
        return ast.Module(body=value)
    else:
        raise ValueError(f"Cannot parse value: {value} with dtype: {dtype} to ast Node")


class BasePyParam:

    def to_ast_node(self, lineno: int, col_offset: int) -> ast.AST:
        """
        Convert PyParam to AST node.
        Args:
            lineno: a line number of the ast Node in the python file
            col_offset: column offset in that line

        Returns:
            node: an AST node
        """
        node = value_to_ast_node(self.value, type)
        node.lineno = lineno
        node.col_offset = col_offset
        return node

    @staticmethod
    @abstractmethod
    def from_ast_node(node: ast.AnnAssign) -> "BasePyParam":
        """Converts AST node to PyParam object

        Args:
            node: an instance of AnnAssign node.

        Returns:
            pyparam: PyParam object
        """
        pass

    def replace(self, **kwargs: Any) -> "BasePyParam":
        """Replace PyParam fields"""
        return dc.replace(self, **kwargs)

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Returns pyparam object as python dictionary.

        Returns:
            config: a python dictionary version of PyParam object
        """
        pass

    @staticmethod
    @abstractmethod
    def from_dict(**kwargs) -> "BasePyParam":
        """
        Create pyparam from python dictionary
        Args:
            config: a python dictionary.

        Returns:
            pyparam: initialized PyParam object
        """
        pass

    @staticmethod
    def parse_args_kwargs_from_node(node: ast.AnnAssign):
        """Extracts PyParam args and kwargs from AST node

        Args:
            node: an instance of AnnAssign node.

        Returns:
            args: a list of PyParam args
            kwargs: a dict with PyParam kwargs
        """
        value_args = node.value.args
        value_keywords = node.value.keywords
        args = []
        keywords = {}
        for arg_node in value_args:
            args.append(ast_node_to_value(arg_node))

        for keyword in value_keywords:
            keywords[keyword.arg] = ast_node_to_value(keyword.value)

        return args, keywords


@dc.dataclass(frozen=True)
class NamedBasePyParam(BasePyParam):
    """A named version of the PyParam - a py param with string name

    Args:
        name: name of the PyParam variable
    """

    name: str

    @property
    @abstractmethod
    def full_name(self) -> str:
        pass

    @property
    @abstractmethod
    def value(self) -> Any:
        pass

    @staticmethod
    @abstractmethod
    def from_ast_node(node: ast.AnnAssign) -> "NamedBasePyParam":
        """Converts AST node to PyParam object

        Args:
            node: an instance of AnnAssign node.

        Returns:
            pyparam: PyParam object
        """
        pass


@dc.dataclass(frozen=True)
class PyParam(BasePyParam):
    """
    PyParam container.

    Args:
        value: a value of the parameter, must be defined statically
        dtype: a python dtype of the value parameter, if not provided it will be
            extracted from type(value)
        scope: a scope of the parameter e.g. 'model/optimizer', 'dataset' etc
        desc: an optional description of the pyparam
    """
    value: Any
    dtype: Optional[type] = None
    scope: Optional[str] = ""
    desc: Optional[str] = ""

    def compile(self) -> "PyParam":
        """
        Compile pyparam. This function is used when some of the pyparam
        parameters are in incorrect format e.g. when we read from yaml file
        dtype will be parsed as a string value.

        Returns:
            pyparam: initialized PyParam object
        """
        try:
            if self.dtype is None:
                dtype = type(self.value)
                return self.replace(dtype=dtype)

            if type(self.dtype) == str:
                dtype = _str_to_dtype.get(self.dtype, None)
                if dtype is None:
                    raise ValueError(f"Unsupported PyParam dtype: {self.dtype}")

                value = dtype(self.value)
                return self.replace(dtype=dtype, value=value)
        except Exception as e:
            raise ValueError(f"Error while compiling pyparam: {self}: {e}")
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Returns pyparam object as python dictionary.

        Returns:
            config: a python dictionary version of PyParam object
        """
        params = {"dtype": self.dtype.__name__, "value": self.value}
        if len(self.desc) != 0:
            params["desc"] = self.desc
        return params

    @staticmethod
    def from_dict(config: Dict[str, Any]) -> "PyParam":
        """
        Create pyparam from python dictionary
        Args:
            config: a python dictionary.

        Returns:
            pyparam: initialized PyParam object
        """
        return PyParam(**config).compile()

    def to_ast_node(self, lineno: int, col_offset: int) -> ast.AST:
        """
        Convert PyParam to AST node.
        Args:
            lineno: a line number of the ast Node in the python file
            col_offset: column offset in that line

        Returns:
            node: an AST node
        """
        node = value_to_ast_node(self.value, self.dtype)
        node.lineno = lineno
        node.col_offset = col_offset
        return node

    @staticmethod
    def from_ast_node(node: ast.AnnAssign) -> "PyParam":
        """Converts AST node to PyParam object

        Args:
            node: an instance of AnnAssign node.

        Returns:
            pyparam: PyParam object
        """
        args, keywords = PyParam.parse_args_kwargs_from_node(node)
        return PyParam(*args, **keywords).compile()

    def render_as_ast_node(self, lineno: int, col_offset: int) -> ast.AST:
        """
        Render PyParam to AST node. This implementation save PyParam as AST Call
        object, so not only value is generated but full PyParam class will be generated
        in the source code.

        Args:
            lineno: a line number of the ast Node in the python file
            col_offset: column offset in that line

        Returns:
            node: an AST node of PyParam object e.g. PyParam(value=4, dtype=int, scope='loop')
        """
        fixed_dtype = self.replace(dtype=_dtype_to_str[self.dtype])
        node = value_to_ast_node(str(fixed_dtype), type)
        node.lineno = lineno
        node.col_offset = col_offset
        return node


@dc.dataclass(frozen=True)
class NamedPyParam(NamedBasePyParam):
    """A named version of the PyParam. The name comes from the PyParam definition
    in the python file. For example if following line is defined in some python
    file:
        pi: float = PyParam(value=3.14159, scope="math/constants", desc="A value of Pi")

    The resulting NamedPyParam will have name="pi", the name is extracted by pyparam
    parser.

    Args:
        name: name of the PyParam variable
        param: an instance of PyParam
    """

    param: PyParam

    def to_dict(self) -> Dict[str, Any]:
        """Returns NamedPyParam as python dict"""
        return self.param.to_dict()

    @staticmethod
    def from_dict(name: str, config: Dict[str, Any]) -> "NamedPyParam":
        """Created NamedPyParam from python dictionary

        Args:
            name: a name of the pyparam variable
            config: a python dictionary with PyParam fields

        Returns:
            param: An instance of NamedPyParam
        """
        return NamedPyParam(name, PyParam.from_dict(config))

    @staticmethod
    def from_ast_node(node: Union[ast.AnnAssign, ast.Assign]) -> "NamedPyParam":
        """Converts AST AnnAssign and Assign nodes to NamedPyParam object"""
        if isinstance(node, ast.AnnAssign):
            return NamedPyParam(name=node.target.id, param=PyParam.from_ast_node(node))
        elif isinstance(node, ast.Assign):

            if len(node.targets) > 1:
                raise NotImplementedError(f"Node {node} has more than one target.")

            return NamedPyParam(
                name=node.targets[0].id,
                param=PyParam.from_ast_node(node))
        else:
            raise NotImplementedError(
                f"AST node type {type(node)} is not supported"
            )

    def to_ast_node(self, lineno: int, col_offset: int) -> ast.AST:
        return self.param.to_ast_node(lineno, col_offset)

    @property
    def scope(self) -> str:
        """Get scope parameter from the PyParam object"""
        return self.param.scope

    @property
    def full_name(self) -> str:
        """Returns full path to the variable by concatenation of the scope
        and name. For example if pyparam scope='scope1/scope2' and param name is
        'variable', then full path is equal to: 'scope1/scope2/variable'.

        Returns:
            full_name: a full path to the variable
        """
        return os.path.join(self.scope, self.name)

    @property
    @abstractmethod
    def value(self) -> Any:
        return self.param.value

    def param_replace(self, **kwargs: Any) -> "NamedPyParam":
        """Replace param fields"""
        return self.replace(param=self.param.replace(**kwargs))
