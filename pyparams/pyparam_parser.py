"""A  implementation of params parser using AST package"""
import ast
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from typing import List, Any, Dict, Tuple, TypeVar, Optional, Union

import astor
import yaml
from astor.source_repr import split_lines

import pyparams.utils as utils
from pyparams.pyparam import (
    NamedPyParam,
    PyParam,
    NamedBasePyParam,
    ast_node_to_value,
)

NamedBasePyParamType = TypeVar("NamedBasePyParamType")
COMPILED_SOURCE_INDENTATION = " " * 2
VERSION_PARAM_KEY_NAME = "version"
YAML_CONFIG_INDENTATION = 4


def pyparams_ordered_yaml_dump(data, stream=None, **kwds):
    """Fixes rendering of OrderedDict in the yaml file"""

    class OrderedDumper(yaml.SafeDumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
        )

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    yaml_string = yaml.dump(
        data, stream=None, Dumper=OrderedDumper, indent=YAML_CONFIG_INDENTATION, **kwds
    )
    yaml_string = utils.convert_desc_field_to_comment(
        yaml_string, indent=YAML_CONFIG_INDENTATION
    )
    return stream.write(yaml_string)


def read_source_code(filepath: Path) -> str:
    """Reads python source code and returns it as a string

    Args:
        filepath: path to file

    Returns:
        source: a content of the file returned as single string
    """
    with open(str(filepath), "r") as file:
        source_code = "".join(file.readlines())
    return source_code


def read_yaml_file(filepath: Path) -> Dict[str, Any]:
    """Read YAML config file

    Args:
        filepath: path to YAML file

    Returns:
        config: a content of the yaml file returned a python dictionary
    """
    with open(str(filepath), "r") as file:
        config_str = utils.convert_comment_to_desc_field("".join(file.readlines()))
        config = yaml.load(config_str, Loader = yaml.FullLoader)
    return config


def astor_pretty_source_formatter(source):
    """ Prettify the source.
    """
    return "".join(split_lines(source, maxline=10e6))


def find_pyparams_assignments_nodes(
    node: ast.Module, assigment_op_name: str = PyParam.__name__
) -> List[Union[ast.AnnAssign, ast.Assign]]:
    """Scans the AST Module i.e. an AST representation of the python file and
    return all AnnAssign nodes.
    Note that AnnAssign appears when pyparam is defined with typing annotation e.g.

    variable_a: int = PyParam(value=512) # is a AnnAssign node
    variable_a = PyParam(value=512) # is a Assign node

    Args:
        node: a root node of the AST tree, this node should be a AST representation
            of the python file
        assigment_op_name: a name of the assignment function e.g. PyParam.__name__

    Returns:
        nodes: a list of AnnAssign or Assign found in the Module

    """

    supported_nodes = [ast.AnnAssign, ast.Assign]

    pyparams_nodes = []
    for element in node.body:
        if element.__dict__.get("body", None) is not None:
            pyparams_nodes += find_pyparams_assignments_nodes(
                element, assigment_op_name=assigment_op_name
            )

        # dealing with function definition arguments
        if isinstance(element, ast.FunctionDef):

            defaults = element.args.defaults
            num_defaults = len(defaults)
            args = element.args.args[-num_defaults:]
            arg_nodes = []
            for arg, default in zip(args, defaults):
                arg_nodes.append(ast.Assign(
                    targets=[ast.Name(arg.arg, None)], value=default)
                )

            body_element = ast.Module(arg_nodes)
            pyparams_nodes += find_pyparams_assignments_nodes(
                body_element, assigment_op_name=assigment_op_name
            )

        # must be AnnAssign
        if any([isinstance(element, sn) for sn in supported_nodes]):
            # value must be Call
            if isinstance(element.value, ast.Call):
                # func must be named
                if isinstance(element.value.func, ast.Name):
                    func_id = element.value.func.id
                    # the name of the function must be e.g. "PyParam"
                    if func_id == assigment_op_name:
                        pyparams_nodes += [element]
                    else:
                        # loop over the arguments of some Func(**kwargs) declaration
                        # note only named keywords are supported
                        kwarg_nodes = []
                        for keyword in element.value.keywords:
                            kwarg_nodes.append(
                                ast.Assign(
                                    targets=[ast.Name(keyword.arg, None)],
                                    value=keyword.value
                                )
                            )

                        body_element = ast.Module(kwarg_nodes)
                        pyparams_nodes += find_pyparams_assignments_nodes(
                            body_element, assigment_op_name=assigment_op_name
                        )

    return pyparams_nodes


def find_function_def_nodes(node: ast.Module) -> List[ast.FunctionDef]:
    """Finds ast.FunctionDef nodes in the source code. ast.FunctionDef
    represents `def function_name(....):` statement in the code.

    Args:
        node: a root node of the AST tree, this node should be a AST representation
            of the python file

    Returns:
        nodes: a list of ast.FunctionDef found in the whole Module
    """
    pyparams_nodes = []
    for element in node.body:
        if type(element) == ast.FunctionDef:
            pyparams_nodes.append(element)
            pyparams_nodes += find_function_def_nodes(element)
    return pyparams_nodes


def find_ast_expr_nodes(node: ast.Module, assigment_op_name: str) -> List[ast.Expr]:
    """Finds all ast.Expr nodes which name match assigment_op_name.

    Args:
        node: a root node of the AST tree, this node should be a AST
            representation of the python file
        assigment_op_name: a name of the expression to find e.g. IncludeSource

    Returns:
        nodes: a list of ast.Call found in the whole Module which
            func.name matches `assigment_op_name`
    """
    pyparams_nodes = []
    for element in node.body:
        if type(element) == ast.FunctionDef:
            pyparams_nodes += find_ast_expr_nodes(
                element, assigment_op_name=assigment_op_name
            )
        if type(element) == ast.Expr:
            if type(element.value) == ast.Call:
                if ast_node_to_value(element.value.func) == assigment_op_name:
                    pyparams_nodes.append(element)

    return pyparams_nodes


def get_all_pyparams_from_source_code(
    source: str,
    assigment_op_name: str = PyParam.__name__,
    ast_parser: NamedBasePyParamType = NamedPyParam,
) -> List[NamedBasePyParamType]:
    """Reads all params from the source code

    Args:
        source: a string representation of the python file
        assigment_op_name: a name of the assignment operation e.g. "PyParam"
        ast_parser: a class with function from_ast_node(node)

    Returns:
        params: a list NamedPyParam found in the source code.
    """

    root_module = ast.parse(source=source)
    pyparams_nodes = find_pyparams_assignments_nodes(
        root_module, assigment_op_name=assigment_op_name
    )
    return [ast_parser.from_ast_node(node) for node in pyparams_nodes]


def get_source_params_assignments(
    source: str,
    assigment_op_name: str = PyParam.__name__,
    ast_parser: NamedBasePyParamType = NamedPyParam,
) -> Tuple[Dict[str, ast.AnnAssign], ast.Module]:
    """Find all AnnAssign in the source code.

    Args:
        source: a string representation of the python file
        assigment_op_name: a name of the assignment function e.g. PyParam.__name__
        ast_parser: a class with function from_ast_node(node) and full_name property

    Returns:
        named_nodes: a dictionary with {pyparam.full_name: AnnAssign}
        source_code_module: a root AST Module of the source code
    """
    source_code_module = ast.parse(source=source)
    pyparams_nodes = find_pyparams_assignments_nodes(
        source_code_module, assigment_op_name=assigment_op_name
    )

    named_nodes = {}
    for node in pyparams_nodes:
        pyparam: NamedBasePyParam = ast_parser.from_ast_node(node)
        named_nodes[pyparam.full_name] = node

    return named_nodes, source_code_module


def params_to_yaml_config(
    config_params: List[NamedBasePyParam], save_file_path: Path
) -> None:
    """Convert list of params to the YAML file

    Args:
        config_params: a list of NamedPyParam
        save_file_path: path location of the YAML file

    """
    save_file_path = str(save_file_path)

    config_params_dict = {param.full_name: param for param in config_params}
    params_tree = OrderedDict()

    def insert_node(sc: str, param: NamedBasePyParam, config: Dict[str, Any]) -> None:
        nodes = sc.split("/")
        if len(nodes) > 1:
            head, tail = nodes[0], "/".join(nodes[1:])
            if head not in config:
                config[head] = OrderedDict()
            insert_node(tail, param, config[head])
        else:
            if len(sc) > 0:
                if sc not in config:
                    config[sc] = OrderedDict()

                config[sc][param.name] = param.to_dict()
            else:
                config[param.name] = param.to_dict()
            return

    for scope, params in config_params_dict.items():
        head = "/".join(scope.split("/")[:-1])
        insert_node(head, params, params_tree)

    with open(save_file_path, "w") as outfile:
        pyparams_ordered_yaml_dump(
            params_tree, stream=outfile, width=60, default_flow_style=False
        )


def source_to_yaml_config(source: str, save_file_path: Path) -> None:
    """Extracts pyparams from the source and save them as yaml config

    Args:
        source:  a string representation of the python file
        save_file_path: path location of the YAML file

    """
    config_params = get_all_pyparams_from_source_code(source)
    params_to_yaml_config(config_params=config_params, save_file_path=save_file_path)


def read_params_from_config(config: dict, _root_name: str = "") -> List[NamedPyParam]:
    """Reads params from the nested python dictionary.

    Args:
        config: a python dictionary with params definitions
        _root_name: used internally

    Returns:
        params a list of NamedPyParam extracted from the dictionary
    """

    def _is_end_node(node: Dict[str, Any]) -> bool:
        """Checks whether node is an end node i.e. contains PyParam definition"""
        return "value" in node and "dtype" in node

    params = []
    for name, node in config.items():
        if _is_end_node(node):
            # extract scope from the full path. Note: _root_name.split("/")[0] == "/"
            node["scope"] = "/".join(_root_name.split("/")[1:])
            params += [NamedPyParam.from_dict(name, node)]
        else:
            params += read_params_from_config(node, "/".join([_root_name, name]))
    return params


def compile_source_code(
    source_code: str,
    config: dict,
    assigment_op_name: str = PyParam.__name__,
    ast_parser: NamedBasePyParamType = NamedPyParam,
    validate_version: bool = False,
) -> str:
    """Compile the source code with parameter definition in the config file.

    Args:
        source_code: a string representation of the python file
        config: a python dictionary with params definitions
        assigment_op_name: a name of the assignment function e.g. PyParam.__name__
        ast_parser: a class with function from_ast_node(node) and full_name property
        validate_version: look for the "version" parameter and compare the
            source_code version with config version. If both will differ
            a ValueError will be raised.

    Returns:
        compiled_source: a string representation of the compiled source code.
    """
    config_params = read_params_from_config(config)

    return compile_source_code_from_configs_list(
        source_code=source_code,
        config_params=config_params,
        assigment_op_name=assigment_op_name,
        ast_parser=ast_parser,
        validate_version=validate_version,
    )


def get_default_compile_node_transformer(
    node_to_param: Dict[ast.AnnAssign, NamedBasePyParamType]
) -> ast.NodeTransformer:
    """
    This AST node transformer changes Pyparam to its value e.g.

        x: int = PyParam(5, int)

    will be replaced with:
        x: int = 5

    Args:
        node_to_param: a dict which maps AST Node with PyParam assignment to
            its NamedPyParam (python) representation

    Returns:
        Node transformer
    """

    class DefaultASTTransformer(ast.NodeTransformer):
        def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
            """
            For nodes: replace with static value
            """

            if node in node_to_param:
                params = node_to_param[node]
                node.value = params.to_ast_node(
                    lineno=node.value.lineno, col_offset=node.value.col_offset
                )
                return node
            else:
                return node

        def visit_Assign(self, node: ast.Assign) -> ast.AST:
            """
            For nodes: replace with static value
            """

            if node in node_to_param:
                params = node_to_param[node]
                node.value = params.to_ast_node(
                    lineno=node.value.lineno, col_offset=node.value.col_offset
                )
                return node
            elif isinstance(node.value, ast.Call) and len(node.value.keywords) > 0:
                new_keywords = []
                for keyword in node.value.keywords:
                    for n, p in node_to_param.items():
                        if n.value == keyword.value:
                            keyword.value = p.to_ast_node(
                                lineno=keyword.value.lineno,
                                col_offset=keyword.value.col_offset
                            )
                    new_keywords.append(keyword)
                node.value.keywords = new_keywords
                return node
            else:
                return node

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
            """
            For nodes: replace with static value
            """

            defaults = node.args.defaults
            num_defaults = len(defaults)
            args = node.args.args[-num_defaults:]

            new_defaults = []
            for arg, default in zip(args, defaults):
                for n, p in node_to_param.items():
                    if n.value == default:
                        new_default = p.to_ast_node(
                            lineno=default.lineno,
                            col_offset=default.col_offset
                        )
                        new_defaults.append(new_default)
            node.args.defaults = new_defaults  # transform function arguments assignments
            # traverse subsequent nodes
            return self.generic_visit(node)

    return DefaultASTTransformer()


def get_render_as_ast_node_transformer(
    node_to_param: Dict[ast.AnnAssign, NamedPyParam]
) -> ast.NodeTransformer:
    """
    This AST node transformer changes Pyparam to any other pyparam:

        x: int = PyParam(5, int)

    assuming that: node_to_param[node] = PyParam(15, int, desc='some desc')
    will result in:
        x: int = PyParam(15, int, desc='some desc')

    Args:
        node_to_param: a dict which maps AST Node with PyParam assignment to
            its NamedPyParam (python) representation, this representation
            may contain different values

    Returns:
        Node transformer
    """
    # transforming nodes with values from config
    class ASTTransformer(ast.NodeTransformer):
        def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
            """
            For nodes: replace with static value
            """
            if node in node_to_param:
                node.value = node_to_param[node].param.render_as_ast_node(
                    lineno=node.value.lineno, col_offset=node.value.col_offset
                )
                return node
            else:
                return node

    return ASTTransformer()


def compile_source_code_from_configs_list(
    source_code: str,
    config_params: List[NamedBasePyParamType],
    assigment_op_name: str = PyParam.__name__,
    ast_parser: NamedBasePyParamType = NamedPyParam,
    validate_version: bool = False,
    node_transformer: Optional[ast.NodeTransformer] = None,
) -> str:
    """Compile the source code with parameter definition in the config file.

    Args:
        source_code: a string representation of the python file
        config_params: a list with NamedBasePyParam
        assigment_op_name: a name of the assignment function e.g. PyParam.__name__
        ast_parser: a class with function from_ast_node(node) and full_name property
        validate_version: look for the "version" parameter and compare the
            source_code version with config version. If both will differ
            a ValueError will be raised.
        node_transformer:

    Returns:
        compiled_source: a string representation of the compiled source code.
    """
    named_nodes, root_module = get_source_params_assignments(
        source_code, assigment_op_name=assigment_op_name, ast_parser=ast_parser
    )

    node_to_config_param = {}
    for named_param in config_params:
        node_to_config_param[named_nodes[named_param.full_name]] = named_param

    if validate_version:
        if VERSION_PARAM_KEY_NAME not in named_nodes:
            raise ValueError(
                f"Python template file does not "
                f"contain `{VERSION_PARAM_KEY_NAME}` template parameter."
            )

        if VERSION_PARAM_KEY_NAME not in [param.name for param in config_params]:
            raise ValueError(
                f"Config must have defined `{VERSION_PARAM_KEY_NAME}` field."
            )

        config_version = {param.name: param.value for param in config_params}[
            VERSION_PARAM_KEY_NAME
        ]

        source_code_version = NamedPyParam.from_ast_node(
            named_nodes[VERSION_PARAM_KEY_NAME]
        ).param.value

        if config_version != source_code_version:
            raise ValueError(
                f"Config version: `{config_version}` does not match "
                f"template version: `{source_code_version}`"
            )

    if node_transformer is None:
        node_transformer = get_default_compile_node_transformer(node_to_config_param)

    new_root_module = node_transformer.visit(root_module)
    return astor.to_source(
        new_root_module,
        indent_with=COMPILED_SOURCE_INDENTATION,
        pretty_source=astor_pretty_source_formatter,
    )


def update_source_pyparams(source_code: str, new_params: List[NamedPyParam]) -> str:
    """Replace existing pyparams in the source code with new ones. This function
    can be used to e.g. replace scope parameter of each variable in source

    Args:
        source_code: a string source code with pyparams
        new_params: a list of source code pyparams with new values

    Returns:
        new source code with pyparams parameters adapted from new_params list
    """
    pyparams = get_all_pyparams_from_source_code(source_code)
    named_nodes, source_code_module = get_source_params_assignments(source_code)

    node_to_config_param = {}
    for named_param, new_param in zip(pyparams, new_params):
        node_to_config_param[named_nodes[named_param.full_name]] = new_param

    transformer = get_render_as_ast_node_transformer(node_to_config_param)
    new_root_module = transformer.visit(source_code_module)
    new_source = astor.to_source(
        new_root_module,
        indent_with=COMPILED_SOURCE_INDENTATION,
        pretty_source=astor_pretty_source_formatter,
    )
    return new_source


def replace_param(
    param: NamedPyParam,
    config_params: List[NamedPyParam],
    ignore_missing_keys: bool = False,
) -> List[NamedPyParam]:
    """Replace parameter param.full_name in the config_params list with the `param`.
    Parameters are considered equal when their full_name agrees.

    Args:
        param: a new param to be substituted in the config_params
        config_params: a list of NamedPyParam's
        ignore_missing_keys: if True, it skips param which is
            not present in config_params, otherwise exception will be raised

    Returns:
        config_params: a list of NamedPyParam's with replaced parameter.

    Raises:
         ValueError: when config_params does not have param.full_name
    """
    config_params = deepcopy(config_params)
    config_params_dict = {
        config_param.full_name: config_param for config_param in config_params
    }
    if param.full_name not in config_params_dict:
        if not ignore_missing_keys:
            raise ValueError(
                f"Parameter key:`{param.full_name}` not found "
                f"in the config: {config_params_dict.keys()}"
            )
        print(
            f"Ignoring missing parameter:"
            f"\n\tname      = {param.full_name}"
            f"\n\tvalue     = {param.value}"
        )
        return config_params
    else:
        if param.full_name != "version":
            old_value = config_params_dict[param.full_name].value
            new_value = param.value
            if old_value != new_value:
                print(
                    f"Replacing parameter:"
                    f"\n\tname      = {param.full_name}"
                    f"\n\told value = {old_value}"
                    f"\n\tnew value = {new_value}"
                )
            else:
                print(f"Parameter not changed: {param.full_name}")

            config_params_dict[param.full_name] = param

    return list(config_params_dict.values())


def replace_params(
    params_to_replace: List[NamedPyParam],
    config_params: List[NamedPyParam],
    ignore_missing_keys: bool = False,
) -> List[NamedPyParam]:
    """Replace multiple parameters in config_params

    Args:
        params_to_replace: a parameters to be replaced in the config_params
        config_params: a list of NamedPyParam
        ignore_missing_keys: if True, it skips params from new_config which are
            not present in old_config, otherwise exception will be raised

    Returns:
        config_params: new list of NamedPyParam with some of the parameters
            replaced.
    """

    for param in params_to_replace:
        config_params = replace_param(
            param, config_params, ignore_missing_keys=ignore_missing_keys
        )

    return config_params


def substitute_config(
    old_config_path: Path,
    new_config_path: Path,
    output_config_path: Path,
    ignore_missing_keys: bool = False,
    selected_keys: Optional[List[str]] = None
) -> None:
    """Replace parameters in the YAML configs using another YAML config.

    Args:
        old_config_path: a path to the main config in which we want to replace
            parameters
        new_config_path: a path to the config with new parameters to be replaced in
             old_config.
        output_config_path: a path to the output file
        ignore_missing_keys: if True, it skips params from new_config which are
            not present in old_config, otherwise exception will be raised
        selected_keys: a list of selected keys to be replaced if None all keys in
             new_config_path will be used. Note, keys can be subwords, any
             key matching with subword will be considered in substitution.
    """
    print(
        f"PyParams: Copying parameters from {new_config_path} to {old_config_path}, "
        f"ignore-missing is {ignore_missing_keys}."
    )
    old_params = read_params_from_config(read_yaml_file(old_config_path))
    new_params = read_params_from_config(read_yaml_file(new_config_path))

    if selected_keys is None:
        params_to_replace = new_params
    else:
        params_to_replace = []
        for param in new_params:
            if any([key in param.full_name for key in selected_keys]):
                params_to_replace.append(param)

    config_params = replace_params(
        params_to_replace, old_params, ignore_missing_keys=ignore_missing_keys
    )

    params_to_yaml_config(
        config_params=config_params, save_file_path=output_config_path
    )


def get_param(full_name: str, config_params: List[NamedPyParam]) -> NamedPyParam:
    """Get param from config_params list

    Args:
        full_name: a full name of then parameter
        config_params: a list of NamedPyParam

    Returns:
        param: a param from NamedPyParam with full_name

    Raises:
        ValueError: when there is no required param in the config_params
    """
    config_params = deepcopy(config_params)

    config_params_dict = {
        config_param.full_name: config_param for config_param in config_params
    }
    if full_name not in config_params_dict:
        raise ValueError(
            f"Parameter key:`{full_name}` not found "
            f"in the config: {config_params_dict.keys()}"
        )

    return config_params_dict[full_name]


def add_scope(scope: str, config_params: List[NamedPyParam]) -> List[NamedPyParam]:
    """Append scope of variables in the config_params list. The resulting function
    with append `scope` string at the beginning of each pyparam member e.g.

    before:
        PyParam(value=3, dtype='int', scope='param', desc='')
    after with scope='level':
        PyParam(value=3, dtype='int', scope='level/param', desc='')

    Args:
        scope: a string name of the scope to be added to each pyparam
        config_params: a list of pyparams to be scoped

    Returns:
        scoped params
    """
    new_params = []
    for param in config_params:
        new_params.append(param.param_replace(scope=f"{scope}/{param.param.scope}"))
    return new_params
