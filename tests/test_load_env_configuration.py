import unittest

from hypothesis import given, strategies

import app


class TestLoadEnvConfiguration(unittest.TestCase):

    def test_empty(self):
        self.assertDictEqual({}, app._load_config({}.items()))

    def test_not_matching(self):
        self.assertDictEqual({}, app._load_config({'ABC': 'XYZ'}.items()))
        self.assertDictEqual({}, app._load_config({'KEYDRA_CFGABC': 'XYZ'}.items()))
        self.assertDictEqual({}, app._load_config({'X_KEYDRA_CFG_ABC': 'XYZ'}.items()))

    def test_single_level(self):
        self.assertDictEqual({'a': 'XYZ'}, app._load_config({'KEYDRA_CFG_A': 'XYZ'}.items()))

    def test_multi_level(self):
        self.assertDictEqual({'a': {'b': {'c': 'XYZ'}}}, app._load_config({'KEYDRA_CFG_A_B_C': 'XYZ'}.items()))

    def test_multi_level_merge(self):
        self.assertDictEqual({'a': {'b': {
            'c1': 'X1',
            'c2': 'X2',
            'c3': 'X3'
        }}}, app._load_config(
            {
                'KEYDRA_CFG_A_B_C1': 'X1',
                'KEYDRA_CFG_A_B_C2': 'X2',
                'KEYDRA_CFG_A_B_C3': 'X3',
            }.items()))

    @given(strategies.dictionaries(min_size=1,
                                   keys=strategies.from_regex(r'^KEYDRA_CFG(_[A-Z])+'),
                                   values=strategies.text(min_size=1)))
    def test_merging_env_vars_by_prefix(self, env_vars: dict):
        config = app._load_config(env_vars=env_vars.items())
        self.assertTrue(0 < len(config.items()) <= len(env_vars.items()))

    @given(strategies.dictionaries(min_size=1,
                                   max_size=1,
                                   keys=strategies.from_regex(r'^KEYDRA_CFG(_[A-Z])+'),
                                   values=strategies.text(min_size=1)))
    def test_number_of_nested_levels_driven_by_env_var_naming_convention(self, one_env_var: dict):
        config = app._load_config(env_vars=one_env_var.items())
        expected_number_of_nested_levels = len(list(one_env_var.keys())[0].split('_')) - 2
        produced_number_of_nested_levels = str(config).count(': ')
        self.assertEqual(produced_number_of_nested_levels, expected_number_of_nested_levels)
