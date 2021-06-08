import app
import os
import unittest

from unittest.mock import MagicMock, patch


class TestLambda(unittest.TestCase):
    def setUp(self):
        pass

    @patch('keydra.keydra.Keydra.rotate_and_distribute')
    @patch('app._load_keydra_config')
    def test_lambda_handler_success(self, lkc, rad: MagicMock):
        rotation_result = [
            {'rotate_secret': 'success', 'distribute_secret': 'success'}]
        rad.return_value = rotation_result

        result = app.lambda_handler(event={'trigger': 'adhoc'}, context=None)

        self.assertEqual(result, rotation_result)

    @patch('keydra.keydra.Keydra.rotate_and_distribute')
    @patch('app._load_keydra_config')
    def test_lambda_handler_failure(self, lkc, rad):
        rotation_result = [
            {'rotate_secret': 'fail'}]
        rad.return_value = rotation_result

        with self.assertRaises(Exception):
            app.lambda_handler(event={'trigger': 'adhoc'}, context=None)

    @patch.dict(
        os.environ,
        {
            'KEYDRA_CFG_PROVIDER': 'provider',
            'KEYDRA_CFG_CONFIG_ACCOUNTUSERNAME': 'acct_user',
            'KEYDRA_CFG_CONFIG_SECRETS_REPOSITORY': 'sec_repo',
            'KEYDRA_CFG_CONFIG_SECRETS_PATH': 'sec_path',
            'KEYDRA_CFG_CONFIG_SECRETS_FILETYPE': 'yaml',
            'KEYDRA_CFG_CONFIG_ENVIRONMENT_REPOSITORY': 'env_repo',
            'KEYDRA_CFG_CONFIG_ENVIRONMENT_PATH': 'env_path',
            'KEYDRA_CFG_CONFIG_ENVIRONMENTS_FILETYPE': 'yaml'
        }
    )
    def test__load_env_config(self):
        config = app._load_env_config()

        self.assertEqual(
            config,
            {
                'config': {
                    'accountusername': 'acct_user',
                    'secrets': {
                        'repository': 'sec_repo',
                        'filetype': 'yaml',
                        'path': 'sec_path'
                    },
                    'environments': {
                        'filetype': 'yaml',
                        'repository': 'keydraconfiguration',
                        'path': 'config/environments.yaml'
                    },
                    'environment': {
                        'repository': 'env_repo',
                        'path': 'env_path'
                    }
                },
                'provider': 'provider'
            }
        )
