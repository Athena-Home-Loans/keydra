import json
import unittest

from keydra import loader

from keydra.exceptions import InvalidSecretProvider

from unittest.mock import MagicMock
from unittest.mock import patch


class TestLoader(unittest.TestCase):
    def setUp(self):
        loader.SESSION = MagicMock()
        loader.SECRETS_MANAGER = MagicMock()

    @patch('keydra.loader.SECRETS_MANAGER.get_secret_value')
    def test_fetch_provider_creds_no_key_name(self, mk_sm):
        secret_string = 'secret'
        mk_sm.return_value = secret_string
        key_id = '{}/iam'.format(loader.KEYDRA_SECRETS_PREFIX)

        creds = loader.fetch_provider_creds('iam', None)

        mk_sm.assert_called_once_with(key_id)
        self.assertEqual(creds, secret_string)

    @patch('keydra.loader.SECRETS_MANAGER.get_secret_value')
    def test_fetch_provider_creds_good_json(self, mk_sm):
        secret_string = '{"a": "b"}'
        mk_sm.return_value = secret_string
        key_id = '{}/iam/key'.format(loader.KEYDRA_SECRETS_PREFIX)

        creds = loader.fetch_provider_creds('iam', 'key')

        mk_sm.assert_called_once_with(key_id)
        self.assertEqual(creds, json.loads(secret_string))

    @patch('keydra.loader.SECRETS_MANAGER.get_secret_value')
    def test_fetch_provider_creds_bad_json(self, mk_sm):
        secret_string = 'secret'
        mk_sm.return_value = secret_string
        key_id = '{}/iam/key'.format(loader.KEYDRA_SECRETS_PREFIX)

        creds = loader.fetch_provider_creds('iam', 'key')

        mk_sm.assert_called_once_with(key_id)
        self.assertEqual(creds, secret_string)

    def test_load_provider_client_exists(self):
        c = loader.load_provider_client('iam')

        self.assertEqual(c.__name__, 'Client')

    def test_load_client_exists(self):
        c = loader.load_client('secretsmanager')

        self.assertEqual(c.__name__, 'SecretsManagerClient')

    def test_load_provider_client_does_not_exist(self):
        with self.assertRaises(InvalidSecretProvider):
            loader.load_provider_client('not_a_provider_here_go_away')

    def test_load_client_does_not_exist(self):
        with self.assertRaises(InvalidSecretProvider):
            loader.load_client('not_a_provider_here_go_away')

    @patch('keydra.loader.load_provider_client')
    @patch('keydra.loader.fetch_provider_creds')
    def test_build_client_rotation(self, mk_fpc, mk_ldc):
        mock_client = MagicMock()
        mk_ldc.return_value = mock_client
        mk_fpc.return_value = 'creds'

        loader.build_client('provider_name', 'key')

        mk_ldc.assert_called_once_with('provider_name')
        mk_fpc.assert_called_once_with('provider_name', 'key')

        mock_client.assert_called_once_with(
            session=loader.SESSION,
            credentials='creds',
            region_name=loader.DEFAULT_REGION_NAME
        )

    @patch('keydra.loader.load_provider_client')
    @patch('keydra.loader.fetch_provider_creds')
    def test_build_client_distribution(self, mk_fpc, mk_ldc):
        mock_client = MagicMock()
        mk_ldc.return_value = mock_client
        mk_fpc.return_value = 'creds'

        loader.build_client('provider_name', None)

        mk_ldc.assert_called_once_with('provider_name')
        mk_fpc.assert_called_once_with('provider_name', None)

        mock_client.assert_called_once_with(
            session=loader.SESSION,
            credentials='creds',
            region_name=loader.DEFAULT_REGION_NAME
        )
