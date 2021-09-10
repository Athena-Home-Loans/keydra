import unittest
import json

from keydra.providers import splunk

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from unittest.mock import MagicMock
from unittest.mock import patch

SPLUNK_CREDS = {
    "username": "admin_key",
    "password": "test"
}

SPLUNK_SPEC = {
    'description': 'Test',
    'key': 'keydra/splunk',
    'config': {
        'host': '127.0.0.1'
    },
    'provider': 'splunk',
    'rotate': 'nightly'
}


SF_CREDS = {
  "provider": "salesforce",
  "key": "splunk.api@corp.com.au.dev11",
  "secret": "abcdefghijklmnopqrstuvwxyz1234567890",
  "token": "abcdefghijklmnopqrstuvwxyz",
  "env": "dev11",
  "domain": "test"
}

DEST = {
    'provider': 'splunk',
    'source': {
        'username': 'key',
        'password': 'secret',
        'token': 'token'
    },
    'key': 'Dev',
    'config': {
        'app': 'Splunk_TA_Dummy',
        'path': 'account',
        'host': '127.0.0.1',
        'appconfig': {
            'auth_type': 'basic',
            'endpoint': 'test.salesforce.com',
            'output_mode': 'json',
            'sfdc_api_version': '48.0',
        }
    },
    'envs': ['prod']
}


class TestProviderSplunk(unittest.TestCase):
    @patch.object(splunk, 'SplunkClient')
    def test__rotate_account_one_dest(self,  mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)
        cli._smclient = MagicMock()
        cli._generate_splunk_passwd(2).return_value = "aaa"
        mk_splunk().tokenauth = False

        cli._rotate_secret(SPLUNK_SPEC)

        self.assertEqual(mk_splunk().change_passwd.call_count, 1)

    @patch.object(splunk, 'SplunkClient')
    def test__rotate_token(self,  mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)
        cli._smclient = MagicMock()
        mk_splunk().tokenauth = True

        cli._rotate_secret(SPLUNK_SPEC)

        self.assertEqual(mk_splunk().rotate_token.call_count, 1)

    @patch.object(splunk.Client, '_rotate_secret')
    def test_rotate(self, mk_rotate_secret):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        cli.rotate('something')

        mk_rotate_secret.assert_called_once_with('something')

    def test__redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'username': 'KEY_ID',
                'password': 'THIS_IS_SECRET'
            }
        }

        r_result = splunk.Client.redact_result(result)
        r_value = r_result['value']['password']

        self.assertNotEqual(r_value, 'THIS_IS_SECRET')

    def test__redact_result_no_secret(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = splunk.Client.redact_result(result)

        self.assertEqual(r_result, result)

    def test_validate_spec_bad_domain(self):
        spec_bad_domain = {
            'description': 'Test',
            'key': 'keydra/splunk',
            'config': {
                'host': 'corp.com/com.corp'
            },
            'provider': 'splunk',
            'rotate': 'nightly'
        }

        r_result = splunk.Client.validate_spec(spec_bad_domain)

        self.assertEqual(r_result, (False,
                         'Host {} must be a valid IP or domain name'.format(
                            spec_bad_domain['config']['host'])))

    def test_validate_spec_bad_ip(self):
        spec_bad_ip = {
            'description': 'Test',
            'key': 'keydra/splunk',
            'config': {
                'host': '10.256.0.1'
            },
            'provider': 'splunk',
            'rotate': 'nightly'
        }

        r_result_1 = splunk.Client.validate_spec(spec_bad_ip)

        self.assertEqual(r_result_1, (False,
                         'Host {} must be a valid IP or domain name'.format(
                                            spec_bad_ip['config']['host'])))

    @patch.object(splunk, 'SplunkClient')
    def test__rotate_except(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        mk_splunk().change_passwd.side_effect = Exception('Boom!')
        mk_splunk().tokenauth = False

        cli._generate_splunk_passwd(32).return_value = "aaaabbbbcccc"

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPLUNK_SPEC)

    @patch.object(splunk, 'SplunkClient')
    def test__change_splunk_pass_except(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        mk_splunk().change_passwd.side_effect = Exception('woot')
        mk_splunk().tokenauth = False

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPLUNK_SPEC)

    @patch.object(splunk, 'SplunkClient')
    def test__distribute(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SPLUNK_CREDS)

        mk_splunk().update_app_config.return_value = 200

        d_result = cli._distribute(secret=SF_CREDS, destination=DEST)

        self.assertEqual(d_result, DEST)

    @patch.object(splunk, 'SplunkClient')
    def test__distribute_app_not_installed(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SPLUNK_CREDS)

        mk_splunk()._app_exists.return_value = False

        with self.assertRaises(DistributionException):
            cli._distribute(secret=SF_CREDS, destination=DEST)

    def test__splunk_connect_error(self):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SPLUNK_CREDS)

        cli._check_app_exists = MagicMock()
        cli._check_app_exists.return_value = True

        cli._splunk_client = MagicMock()
        cli._splunk_client.side_effect = Exception

        with self.assertRaises(DistributionException):
            cli._distribute(secret=SF_CREDS, destination=DEST)

    def test__distribute_bad_sm_creds(self):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        cli._smclient = MagicMock()
        cli._splunk_client = MagicMock()
        cli._smclient.get_secret_value.return_value = "so not json"

        with self.assertRaises(DistributionException):
            cli._distribute(secret=SF_CREDS, destination=DEST)

    @patch.object(splunk, 'SplunkClient')
    def test__app_create_fail(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SPLUNK_CREDS)

        mk_splunk().update_app_config.return_value.status = 400

        with self.assertRaises(DistributionException):
            cli._distribute(secret=SF_CREDS, destination=DEST)

    @patch.object(splunk, 'SplunkClient')
    def test__no_session(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=None,
                            region_name='ap-southeast-2', verify=False)

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SPLUNK_CREDS)

        mk_splunk().update_app_config.return_value.status = 400

        with self.assertRaises(DistributionException):
            cli._distribute(secret=SF_CREDS, destination=DEST)

    @patch.object(splunk, 'SplunkClient')
    def test__update_fail(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=None,
                            region_name='ap-southeast-2', verify=False)

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SPLUNK_CREDS)

        mk_splunk().update_app_config.side_effect = Exception

        with self.assertRaises(DistributionException):
            cli._distribute(secret=SF_CREDS, destination=DEST)

    @patch.object(splunk, 'SplunkClient')
    def test__update_fail2(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=None,
                            region_name='ap-southeast-2', verify=False)

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SPLUNK_CREDS)

        mk_splunk().update_app_storepass.side_effect = Exception

        with self.assertRaises(DistributionException):
            cli._distribute(secret=SF_CREDS, destination=DEST)
