"""Tests for tools.pyparam_parser.py"""

import ast
import tempfile
import unittest
from pathlib import Path

import astor

from pyparams import get_project_root_path
from pyparams import pyparam_parser
from pyparams.pyparam import PyParam, NamedPyParam


class ParserFunctionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.sample_path = get_project_root_path() / "resources/code_samples"
        self.config_tmp_path = Path(f"{self.tmp_dir}/test.yaml")
        self.source_code_tmp_path = Path(f"{self.tmp_dir}/compiled.py")

    def test_find_pyparams_assignments(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "template1.py")
        root = ast.parse(source=source_code)
        pyparam_nodes = pyparam_parser.find_pyparams_assignments_nodes(root)
        self.assertEqual(len(pyparam_nodes), 2)

    def test_ast_assign_to_pyparam(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "template1.py")
        root = ast.parse(source=source_code)
        pyparam_nodes = pyparam_parser.find_pyparams_assignments_nodes(root)

        pyparam = NamedPyParam.from_ast_node(pyparam_nodes[0])

        exp_param = NamedPyParam(
            "start_index", PyParam(1, int, scope="loop", desc="summation start index")
        )
        self.assertEqual(pyparam, exp_param)

        pyparam = NamedPyParam.from_ast_node(pyparam_nodes[1])
        exp_param = NamedPyParam(
            "max_iters", PyParam(6, int, "loop", "max number of iterations")
        )
        self.assertEqual(pyparam, exp_param)

    def test_dict_dtype_pyparam(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "template6.py")
        root = ast.parse(source=source_code)
        pyparam_nodes = pyparam_parser.find_pyparams_assignments_nodes(root)

        pyparam = NamedPyParam.from_ast_node(pyparam_nodes[0])

        exp_param = NamedPyParam(
            name="foo1_dict",
            param=PyParam(
                value={"a": 1, "b": 2}, dtype=dict, scope="model", desc="foo1"
            ),
        )
        self.assertEqual(pyparam, exp_param)

        pyparam = NamedPyParam.from_ast_node(pyparam_nodes[1])
        exp_param = NamedPyParam(
            name="foo2_dict",
            param=PyParam(
                value={"a": [1, 1, 2]}, dtype=dict, scope="model", desc="foo2"
            ),
        )

        self.assertEqual(pyparam, exp_param)

        pyparam = NamedPyParam.from_ast_node(pyparam_nodes[2])
        exp_param = NamedPyParam(
            name="foo3_dict",
            param=PyParam(
                value={"a": {"aa": 3, "ab": [1, 3]}, "b": [1, 2, 3], "c": "test"},
                dtype=dict,
                scope="model",
                desc="foo2",
            ),
        )
        self.assertEqual(pyparam, exp_param)

        pyparam = NamedPyParam.from_ast_node(pyparam_nodes[3])

        exp_param = NamedPyParam(
            name="foo4_dict",
            param=PyParam(
                value=[
                    {"a": {"aa": 3, "ab": [1, 3]}, "b": [1, 2, 3], "c": "test"},
                    {"A": {"AA": 15., "AB": [1]}, "B": [2, 3], "C": "TEST"},
                ],
                dtype=list,
                scope="model",
                desc="foo4 nested dict in list",
            ),
        )
        self.assertEqual(pyparam, exp_param)

        source_code = pyparam_parser.read_source_code(self.sample_path / "template6.py")
        pyparam_parser.source_to_yaml_config(source_code, self.config_tmp_path)
        config = pyparam_parser.read_yaml_file(Path(self.config_tmp_path))

        pyparam_parser.compile_source_code(source_code, config, validate_version=False)

    def test_get_all_pyparams_from_source_code(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "template1.py")
        pyparams = pyparam_parser.get_all_pyparams_from_source_code(source_code)

        exp_params = [
            NamedPyParam(
                "start_index",
                PyParam(1, int, scope="loop", desc="summation start index"),
            ),
            NamedPyParam(
                "max_iters", PyParam(6, int, "loop", "max number of iterations")
            ),
        ]

        self.assertEqual(pyparams, exp_params)

    def test_to_yaml(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "template3.py")
        pyparam_parser.source_to_yaml_config(source_code, self.config_tmp_path)

    def test_loading_yaml(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "template3.py")
        pyparam_parser.source_to_yaml_config(source_code, self.config_tmp_path)

        config = pyparam_parser.read_yaml_file(Path(self.config_tmp_path))
        params = pyparam_parser.read_params_from_config(config)

        exp_params = [
            NamedPyParam(
                name="version",
                param=PyParam(value="1.0", dtype=str, scope="", desc="model version"),
            ),
            NamedPyParam(
                name="base_num_filters",
                param=PyParam(value=4, dtype=int, scope="feature_extractor", desc=""),
            ),
            NamedPyParam(
                name="include_root",
                param=PyParam(
                    value=False, dtype=bool, scope="feature_extractor", desc=""
                ),
            ),
            NamedPyParam(
                name="regularize_depthwise",
                param=PyParam(
                    value=False, dtype=bool, scope="feature_extractor", desc=""
                ),
            ),
            NamedPyParam(
                name="activation_fn_in_separable_conv",
                param=PyParam(
                    value=False, dtype=bool, scope="feature_extractor", desc=""
                ),
            ),
            NamedPyParam(
                name="entry_flow_blocks",
                param=PyParam(
                    value=(1, 1, 1),
                    dtype=tuple,
                    scope="feature_extractor",
                    desc="Number of units in each bock in the entry flow.",
                ),
            ),
            NamedPyParam(
                name="middle_flow_blocks",
                param=PyParam(
                    value=(1,),
                    dtype=tuple,
                    scope="feature_extractor",
                    desc="Number of units in the middle flow.",
                ),
            ),


        ]

        self.assertEqual(params, exp_params)

    def test_source_code_compilation(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "template3.py")
        pyparam_parser.source_to_yaml_config(source_code, self.config_tmp_path)
        config = pyparam_parser.read_yaml_file(Path(self.config_tmp_path))

        new_source_code = pyparam_parser.compile_source_code(
            source_code=source_code, config=config
        )

        with open(self.source_code_tmp_path, "w") as file:
            file.write(new_source_code)

    def test_version_check(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "template3.py")
        config = pyparam_parser.read_yaml_file(self.sample_path / "template3_config.yml")

        new_source_code = pyparam_parser.compile_source_code(
            source_code=source_code, config=config, validate_version=True
        )

        with open(self.source_code_tmp_path, "w") as file:
            file.write(new_source_code)

        with self.assertRaises(ValueError):
            del config["version"]
            pyparam_parser.compile_source_code(
                source_code=source_code, config=config, validate_version=True
            )

        with self.assertRaises(ValueError):
            config["version"] = {}
            config["version"]["value"] = "x"
            config["version"]["dtype"] = "str"
            pyparam_parser.compile_source_code(
                source_code=source_code, config=config, validate_version=True
            )

    def test_get_param(self):
        config = pyparam_parser.read_yaml_file(self.sample_path / "template3_config.yml")
        params_list = pyparam_parser.read_params_from_config(config)
        selected_param = pyparam_parser.get_param("feature_extractor/include_root", params_list)
        param = selected_param.param_replace(value=True)

        exp_param = NamedPyParam(
            name="include_root",
            param=PyParam(value=True, dtype=bool, scope="feature_extractor", desc=""),
        )
        self.assertEqual(param, exp_param)

    def test_replace_param(self):
        config = pyparam_parser.read_yaml_file(self.sample_path / "template3_config.yml")
        config_params = pyparam_parser.read_params_from_config(config)

        param1 = pyparam_parser.get_param(
            "feature_extractor/include_root", config_params
        ).param_replace(value=True)

        param2 = pyparam_parser.get_param(
            "feature_extractor/entry_flow_blocks", config_params
        ).param_replace(value=(1, 1))

        config_params = pyparam_parser.replace_param(param=param1, config_params=config_params)
        config_params = pyparam_parser.replace_param(param=param2, config_params=config_params)

        save_file_path = Path(f"{self.tmp_dir}/config.yaml")
        pyparam_parser.params_to_yaml_config(
            config_params=config_params, save_file_path=save_file_path
        )

        config = pyparam_parser.read_yaml_file(save_file_path)
        params = pyparam_parser.read_params_from_config(config)

        exp_params = [
            NamedPyParam(
                name="activation_fn_in_separable_conv",
                param=PyParam(
                    value=False, dtype=bool, scope="feature_extractor", desc=""
                ),
            ),
            NamedPyParam(
                name="base_num_filters",
                param=PyParam(value=4, dtype=int, scope="feature_extractor", desc=""),
            ),
            NamedPyParam(
                name="entry_flow_blocks",
                param=PyParam(
                    value=(1, 1),
                    dtype=tuple,
                    scope="feature_extractor",
                    desc="Number of units in each bock in the entry flow.",
                ),
            ),
            NamedPyParam(
                name="include_root",
                param=PyParam(
                    value=True, dtype=bool, scope="feature_extractor", desc=""
                ),
            ),
            NamedPyParam(
                name="middle_flow_blocks",
                param=PyParam(
                    value=(1,),
                    dtype=tuple,
                    scope="feature_extractor",
                    desc="Number of units in the middle flow.",
                ),
            ),
            NamedPyParam(
                name="regularize_depthwise",
                param=PyParam(
                    value=False, dtype=bool, scope="feature_extractor", desc=""
                ),
            ),
            NamedPyParam(
                name="version",
                param=PyParam(value="1.0", dtype=str, scope="", desc="model version"),
            ),
        ]

        self.assertEqual(params, exp_params)

    def test_replace_configs(self):
        config = pyparam_parser.read_yaml_file(self.sample_path / "template3_config.yml")
        config_params = pyparam_parser.read_params_from_config(config)
        param1 = pyparam_parser.get_param(
            "feature_extractor/include_root", config_params
        ).param_replace(value=True)
        param2 = pyparam_parser.get_param(
            "feature_extractor/entry_flow_blocks", config_params
        ).param_replace(value=(1, 1))
        param3 = NamedPyParam("some_var", PyParam("test", scope="test_scope"))
        params_to_replace = [param1, param2, param3]

        new_config_params = pyparam_parser.replace_params(
            params_to_replace, config_params=config_params,
            ignore_missing_keys=True
        )
        with self.assertRaises(ValueError):
            pyparam_parser.get_param("test_scope/some_var", new_config_params)

    def test_source_scope_modification(self):

        source_code = pyparam_parser.read_source_code(self.sample_path / "template7.py")
        pyparams = pyparam_parser.get_all_pyparams_from_source_code(source_code)
        named_nodes, source_code_module = pyparam_parser.get_source_params_assignments(source_code)
        scoped_pyparams = pyparam_parser.add_scope("test", pyparams)

        node_to_config_param = {}
        for named_param, new_param in zip(pyparams, scoped_pyparams):
            node_to_config_param[named_nodes[named_param.full_name]] = new_param

        transformer = pyparam_parser.get_render_as_ast_node_transformer(node_to_config_param)
        new_root_module = transformer.visit(source_code_module)
        new_source = astor.to_source(
            new_root_module, indent_with=pyparam_parser.COMPILED_SOURCE_INDENTATION,
            pretty_source=pyparam_parser.astor_pretty_source_formatter
        )
        new_scoped_pyparams = pyparam_parser.get_all_pyparams_from_source_code(new_source)
        self.assertEqual(new_scoped_pyparams, scoped_pyparams)

    def test_update_pyparams(self):

        source_code = pyparam_parser.read_source_code(self.sample_path / "template7.py")
        pyparams = pyparam_parser.get_all_pyparams_from_source_code(source_code)

        scoped_pyparams = pyparam_parser.add_scope("test", pyparams)
        new_source = pyparam_parser.update_source_pyparams(source_code, scoped_pyparams)
        new_scoped_pyparams = pyparam_parser.get_all_pyparams_from_source_code(new_source)
        self.assertEqual(new_scoped_pyparams, scoped_pyparams)

    def test_save_and_load_check_descriptions(self):

        source_code = pyparam_parser.read_source_code(self.sample_path / "template7.py")
        pyparams = pyparam_parser.get_all_pyparams_from_source_code(source_code)
        pyparam_parser.source_to_yaml_config(source_code, self.config_tmp_path)

        config = pyparam_parser.read_yaml_file(self.config_tmp_path)
        loaded_pyparams = pyparam_parser.read_params_from_config(config)

        self.assertEqual(pyparams, loaded_pyparams)
        pyparam_parser.compile_source_code(source_code, config)

    def test_params_wo_annotations_in_functions_def(self):

        source_code = pyparam_parser.read_source_code(self.sample_path / "template9.py")
        pyparams = pyparam_parser.get_all_pyparams_from_source_code(source_code)
        pyparam_parser.source_to_yaml_config(source_code, self.config_tmp_path)
        config = pyparam_parser.read_yaml_file(self.config_tmp_path)
        loaded_pyparams = pyparam_parser.read_params_from_config(config)

        self.assertEqual(pyparams, loaded_pyparams)
        compiled_source = pyparam_parser.compile_source_code(source_code, config)

        self.assertTrue(
            "some_function(x, y, param2: int=2, param3: float=3, "
            "param4: int=4, param5=5, param6=6)" in compiled_source
        )
        self.assertTrue("self, arg1: float=1.1, arg2=2.2" in compiled_source)
        self.assertTrue("result = some_function(0, 1, param2=12, param3=13)" in compiled_source)
        self.assertTrue("  param2 = 2" in compiled_source)
        self.assertTrue("  param3: int = 3" in compiled_source)
        self.assertTrue("  def nested_function2(x, y, np2: int=2)" in compiled_source)
