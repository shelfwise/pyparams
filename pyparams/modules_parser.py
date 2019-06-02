"""Importing python functions/modules"""
import ast
import re
from pathlib import Path
from typing import List

import astor

import pyparams.pyparam as pyparam
import pyparams.pyparam_fn as pyparam_fn
from pyparams import pyparam_parser
from pyparams.module import PyParamModule
from pyparams.pyparam_fn import (
    IncludeModule,
    DeriveModule,
    ReplaceModule,
    IncludeSource,
)
from pyparams.utils import REMatcher


def update_modules_pyparams(source_code: str, new_includes: List[PyParamModule]) -> str:
    """Replace existing pyparams in the source code with new ones. This function
    can be used to e.g. replace scope parameter of each variable in source

    Args:
        source_code: a string source code with pyparams
        new_includes: a list of PyParamModule in with new values

    Returns:
        new source code with pyparams parameters adapted from new_params list
    """
    includes = pyparam_parser.get_all_pyparams_from_source_code(
        source_code, assigment_op_name=IncludeModule.__name__, ast_parser=PyParamModule
    )
    named_nodes, source_code_module = pyparam_parser.get_source_params_assignments(
        source_code, assigment_op_name=IncludeModule.__name__, ast_parser=PyParamModule
    )

    node_to_config_param = {}
    for include, new_include in zip(includes, new_includes):
        node_to_config_param[named_nodes[include.full_name]] = new_include

    # transforming nodes with values from config
    class ASTTransformer(ast.NodeTransformer):
        def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
            """
            For nodes: replace with static value
            """
            if node in node_to_config_param:
                node.value = node_to_config_param[node].render_as_ast_node(
                    lineno=node.value.lineno, col_offset=node.value.col_offset
                )
                return node
            else:
                return node

    new_root_module = ASTTransformer().visit(source_code_module)
    new_source = astor.to_source(
        new_root_module,
        indent_with=pyparam_parser.COMPILED_SOURCE_INDENTATION,
        pretty_source=pyparam_parser.astor_pretty_source_formatter,
    )
    return new_source


def derive_module(source_code: str, search_folders: List[Path]) -> str:
    """Looks for DeriveModule declarations in the code and include the source
    code of the derived module. Source code may contain only single `DeriveModule`
    declaration

    Args:
        source_code: a source code which potentially contains `DeriveModule` declaration
        search_folders: a folders to search for the derived module name.

    Returns:
        a new source code which includes the source of the derived module
    """

    if DeriveModule.__name__ not in source_code:
        return source_code

    if re.split("[()\\s]+", source_code).count(DeriveModule.__name__) != 1:
        raise ValueError("DeriveModule can be used only once in the code")

    derive_module_name = None
    for line in source_code.split("\n"):
        matcher = REMatcher(line)
        if matcher.match(fr'.*{DeriveModule.__name__}.*\([ "]+(.*)[ "]+\).*'):
            derive_module_name = matcher.group(1)

    if derive_module_name is None:
        raise ValueError(
            f"Cannot parse {DeriveModule.__name__} module name. "
            f"Check module source code!"
        )

    print(f"PyParams: deriving module: {derive_module_name}")
    modules_to_derive = pyparam_parser.get_all_pyparams_from_source_code(
        source_code, assigment_op_name=ReplaceModule.__name__, ast_parser=PyParamModule
    )

    new_source = PyParamModule("derived", derive_module_name).find_module_source(
        search_folders
    )

    new_source = include_source_from_nodes(
        source_code=new_source, search_folders=search_folders
    )

    parsed_modules_list = pyparam_parser.get_all_pyparams_from_source_code(
        new_source, assigment_op_name=IncludeModule.__name__, ast_parser=PyParamModule
    )

    modules_list = []
    for module in parsed_modules_list:
        for module_to_use in modules_to_derive:
            if module.name == module_to_use.name:
                print(
                    f"PyParams: deriving module `{module.name}`: {module.path} => {module_to_use.path}"
                )
                module = module_to_use
                break
        modules_list.append(module)

    new_source = update_modules_pyparams(new_source, modules_list)
    return new_source


def render_include_source_code(
    col_offset: int, include_path: str, include_code: str
) -> List[str]:
    """Annotate included source code with additional information about
    the source path of the included source.

    Args:
        col_offset: a col offset of the whole source code which is included
        include_path: a path to the module which is included
        include_code: a content of the module at path `include_path`

    Returns:
        formatted source code
    """
    print(f"PyParams: including module source: {include_path}")
    s_col_offset = " " * col_offset

    comment_line = f"{s_col_offset}PyParams: auto include source of `{include_path}`"
    header_lines = [
        f'{s_col_offset}"""\n{s_col_offset}' + "-" * (80 - col_offset),
        f"{s_col_offset}{comment_line}",
        s_col_offset + "-" * (80 - col_offset) + f'\n{s_col_offset}"""',
    ]

    include_lines = header_lines + [s_col_offset + l for l in include_code.split("\n")]

    comment_line = f"{s_col_offset}INCLUDE END OF `{include_path}`"
    include_lines += [
        f'{s_col_offset}"""\n{s_col_offset}' + "-" * (80 - col_offset),
        f"{s_col_offset}{comment_line}",
        s_col_offset + "-" * (80 - col_offset) + f'\n{s_col_offset}"""',
    ]

    return include_lines


def include_source_from_nodes(source_code: str, search_folders: List[Path]) -> str:
    """Recursively scan a source code for PyParams include and import
    declarations and include the source found modules

    Args:
        source_code: a source code to be parsed
        search_folders: a list of folder in which imported/included modules can be
            found

    Returns:
        formatted source code with included modules
    """
    source_code = parse_include_source_decorators(source_code)
    source_code = parse_include_modules_decorators(source_code)

    if IncludeSource.__name__ not in source_code:
        return source_code

    expr_nodes = pyparam_parser.find_ast_expr_nodes(
        ast.parse(source=source_code), IncludeSource.__name__
    )

    if len(expr_nodes) > 0:
        node = expr_nodes[0]
        expr_data = pyparam.ast_node_to_value(node.value)
        if expr_data["args"]:
            include_path = expr_data["args"][0]
        else:
            include_path = expr_data["keywords"][0][1]

        include_code = PyParamModule("derived", include_path).find_module_source(
            search_folders
        )

        include_lines = render_include_source_code(
            node.col_offset, include_path, include_code
        )

        source_code_lines = source_code.split("\n")
        for lineno, line in enumerate(source_code_lines):
            if IncludeSource.__name__ in line and include_path in line:
                break

        new_source_code_lines = (
            source_code_lines[:lineno] + include_lines + source_code_lines[lineno + 1 :]
        )

        source_code = "\n".join(new_source_code_lines)
        source_code = include_source_from_nodes(source_code, search_folders)

    return source_code


def parse_include_source_decorators(source_code: str) -> str:
    """Look for IMPORT_SOURCE_DECORATOR in the source_code and include selected
    modules to the `source_code`

    Args:
        source_code: input source code which potentially contains `IMPORT_SOURCE_DECORATOR`
            decorators

    Returns:
        new source code with included modules
    """
    if pyparam_fn.IMPORT_SOURCE_DECORATOR not in source_code:
        return source_code

    source_code_lines = source_code.split("\n")
    has_import_source = False
    new_lines = []
    for line in source_code_lines:

        if has_import_source:
            print(f"PyParams: Found include source decorator: {line}")
            has_import_source = False

            matcher = REMatcher(line)
            if matcher.match(r"([ ]*)from (.*).*import.*[*].*"):

                col_offset = matcher.group(1)
                include_source_path = matcher.group(2).strip()
                line = f"{col_offset}{IncludeSource.__name__}('{include_source_path}')"
            else:
                raise ValueError(f"Cannot parse include source line: {line}")

        if pyparam_fn.IMPORT_SOURCE_DECORATOR in line:
            has_import_source = True
            continue

        new_lines.append(line)

    return "\n".join(new_lines)


def parse_include_modules_decorators(source_code: str) -> str:
    """Look for IMPORT_MODULE_DECORATOR in the source_code and include selected
    modules to the `source_code`

    Args:
        source_code: input source code which potentially contains `IMPORT_MODULE_DECORATOR`
            decorators

    Returns:
        new source code with included modules
    """
    if pyparam_fn.IMPORT_MODULE_DECORATOR not in source_code:
        return source_code

    source_code_lines = source_code.split("\n")
    decorator_def = None
    new_lines = []
    for line in source_code_lines:

        if decorator_def:
            print(f"PyParams: Found include module decorator: {line}")
            matcher = REMatcher(line)
            deco_matcher = REMatcher(decorator_def)
            has_deco_match = deco_matcher.match(
                fr".*{pyparam_fn.IMPORT_MODULE_DECORATOR}.*\((.*)\).*"
            )
            if matcher.match(r"([ ]*)import (.*)[ ]*as[ ]*(.*)[ ]*") and has_deco_match:

                dec_scope_arg = deco_matcher.group(1).strip()
                col_offset = matcher.group(1)
                include_source_path = matcher.group(2).strip()
                module_name = matcher.group(3).strip()
                if dec_scope_arg == "":
                    dec_scope_arg = '""'
                line = f"{col_offset}{module_name}: Module = {IncludeModule.__name__}('{include_source_path}', scope={dec_scope_arg})"

            else:
                raise ValueError(
                    f"Cannot parse include module line: {line} with decorator def: {decorator_def}"
                )

            decorator_def = None

        if pyparam_fn.IMPORT_MODULE_DECORATOR in line:
            decorator_def = line
            continue

        new_lines.append(line)

    return "\n".join(new_lines)


def include_modules(source_code: str, search_folders: List[Path]) -> str:
    """Parse source code for possible PyParams modules declarations and generate
    single source which will contain all imported modules

    Args:
        source_code: a source code of file which should be parsed
        search_folders: a list of folder in which imported modules can be found.
            For example ["path/to/models", "path/to/modules"]

    Returns:
        a new source code which will contain all imported modules.
    """
    source_code = derive_module(source_code=source_code, search_folders=search_folders)
    source_code = "from pyparams import Module\n" + source_code
    source_code = include_source_from_nodes(
        source_code=source_code, search_folders=search_folders
    )

    modules_list = pyparam_parser.get_all_pyparams_from_source_code(
        source_code, assigment_op_name=IncludeModule.__name__, ast_parser=PyParamModule
    )

    if len(modules_list) == 0:
        return source_code

    imported_modules = ""
    for module_param in modules_list:
        module_param: PyParamModule

        source = module_param.find_module_source(search_folders=search_folders)

        if module_param.scope != "":
            pyparams = pyparam_parser.get_all_pyparams_from_source_code(source)
            scoped_pyparams = pyparam_parser.add_scope(module_param.scope, pyparams)
            source = pyparam_parser.update_source_pyparams(source, scoped_pyparams)

        source = module_param.encapsulate_source_with_class(source)
        debug_line = (
            f"PyParams: importing `{module_param.path}` as `{module_param.name}`"
        )

        print(debug_line)

        comment_line = f"PyParams:\n\tauto import of `{module_param.path}`\n\tused by: `{module_param.name}`"
        imported_modules += '\n"""\n' + "-" * 80 + "\n"
        imported_modules += f"{comment_line}`\n"
        imported_modules += "-" * 80 + '\n"""\n'
        imported_modules += source

    imported_modules += '\n"""\n' + "-" * 80 + '\n"""\n'

    compiled_source_code = pyparam_parser.compile_source_code_from_configs_list(
        source_code,
        modules_list,
        assigment_op_name=IncludeModule.__name__,
        ast_parser=PyParamModule,
    )

    code = imported_modules + compiled_source_code
    return code
