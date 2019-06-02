"""Tests for tools.pyparam_parser.py"""

import unittest

from pyparams import get_project_root_path
from pyparams import pyparam_parser
import pyparams.modules_parser as mods


class ModulesImportTest(unittest.TestCase):
    def setUp(self):
        self.sample_path = get_project_root_path() / "resources/modules_samples"

    def test_include_module(self):

        source_code = pyparam_parser.read_source_code(self.sample_path / "fun_module_import.py")
        code = mods.include_modules(source_code, [self.sample_path])
        self.assertTrue("class _pyparam_module__matmul2():" in code)
        self.assertTrue("matmul2: Module = _pyparam_module__matmul2()" in code)
        self.assertTrue("    self.matmul = matmul" in code)
        self.assertTrue(
            "offset: float = PyParam(value=1.0, dtype='float', "
            "scope='b/matmul', desc='')" in code)
        self.assertTrue(
            "offset: float = PyParam(value=1.0, dtype='float', "
            "scope='a/matmul', desc='')" in code)

    def test_derive_module(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "derive_module.py")
        code = mods.derive_module(source_code, [self.sample_path])
        self.assertTrue(
            "matmul1: Module = IncludeModule(path='fun_module', scope='a')" in code)
        self.assertTrue(
            "matmul2: Module = IncludeModule(path='fun2_module', scope='c')" in code)

    def test_include_from_derived_module(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "derive_module.py")
        code = mods.include_modules(source_code, [self.sample_path])

        self.assertTrue('bias: float' in code)
        self.assertTrue('beta: float' in code)
        self.assertTrue("scope='c/matmul'" in code)
        self.assertTrue('matmul2: Module = _pyparam_module__matmul2()' in code)

    def test_include_source(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "base_module_test.py")
        code = mods.include_modules(source_code, [self.sample_path])
        self.assertTrue("bias: float = PyParam(1.1, float, 'matmul')" in code)
        self.assertTrue("PyParams: auto include source of `fun2_module`" in code)
        self.assertTrue("INCLUDE END OF `fun_module`" in code)
        self.assertTrue("  return alpha * matrix @ x + offset" in code)
        self.assertTrue("  alpha: float = PyParam(1.0, float, 'matmul')" in code)

    def test_include_source_module_decorators(self):
        source_code = pyparam_parser.read_source_code(self.sample_path / "fun_module_import_decorators.py")
        code = mods.include_modules(source_code, [self.sample_path])