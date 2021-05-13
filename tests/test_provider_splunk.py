import unittest
import json

from keydra.providers import splunk

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from unittest.mock import MagicMock
from unittest.mock import patch

SPLUNK_CREDS = {
    "provider": "splunk",
    "key": "admin_key",
    "secret": "test"
}

SPLUNK_SPEC = {
    'description': 'Test',
    'key': 'keydra/splunk',
    'hosts': ['127.0.0.1'],
    'provider': 'splunk',
    'rotate': 'nightly'
}

MULTI_SPEC = {
    'description': 'Test',
    'key': 'keydra/splunk',
    'hosts': ['127.0.0.1', '10.0.0.1', '172.16.0.1'],
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

        cli._rotate_secret(SPLUNK_SPEC)

        self.assertEqual(mk_splunk().change_passwd.call_count, 1)

    @patch.object(splunk, 'SplunkClient')
    def test__rotate_account_multi_dest(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)
        cli._client = MagicMock()
        cli._rotate_secret(MULTI_SPEC)

        self.assertEqual(mk_splunk().change_passwd.call_count,
                         len(MULTI_SPEC['hosts']))

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
                'provider': 'splunk',
                'key': 'KEY_ID',
                'secret': 'THIS_IS_SECRET'
            }
        }

        r_result = splunk.Client.redact_result(result)
        r_value = r_result['value']['secret']

        self.assertNotEqual(r_value, 'THIS_IS_SECRET')

    def test__redact_result_no_secret(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = splunk.Client.redact_result(result)

        self.assertEqual(r_result, result)

    def test_validate_spec_overlength(self):
        spec_overlength = {
            'description': 'Lorem ipsum dolor sit amet, '
                           'consectetur adipiscing elit, '
                           'sed do eiusmod tempor incididunt'
                           'ut labore et dolore magna'
                           'aliqua. Ut enim ad minim veniam,'
                           'quis nostrud exercitation'
                           ' ullamco laboris nisi ut aliquip'
                           'ex ea commodo consequat. '
                           'Duis aute irure dolor in reprehenderit'
                           'in voluptate velit esse cillum dolore eu'
                           'fugiat nulla pariatur. Excepteur sint'
                           ' occaecat cupidatat non proident, sunt in'
                           'culpa qui officia deserunt mollit anim '
                           'id est laborum.',
            'key': 'keydra/splunk',
            'hosts': ['127.0.0.1'],
            'provider': 'splunk',
            'rotate': 'nightly'
        }

        r_result = splunk.Client.validate_spec(spec_overlength)
        self.assertEqual(r_result, (False,
                         'Value for key description failed length checks'))

    def test_validate_spec_underlength(self):
        spec_underlength = {
            'e': 'e',
            'key': 'keydra/splunk',
            'hosts': ['127.0.0.1'],
            'provider': 'splunk',
            'rotate': 'nightly'
        }

        r_result = splunk.Client.validate_spec(spec_underlength)
        self.assertEqual(r_result, (False, 'Key e failed length checks'))

    def test_validate_spec_bad_domain(self):
        spec_bad_domain = {
            'description': 'Test',
            'key': 'keydra/splunk',
            'hosts': ['corp.com/com.corp'],
            'provider': 'splunk',
            'rotate': 'nightly'
        }

        r_result = splunk.Client.validate_spec(spec_bad_domain)

        self.assertEqual(r_result, (False,
                         'Host {} not valid'.format(
                            spec_bad_domain['hosts'][0])))

    def test_validate_spec_bad_ip(self):
        spec_bad_ip = {
            'description': 'Test',
            'key': 'keydra/splunk',
            'hosts': ['10.256.0.1'],
            'provider': 'splunk',
            'rotate': 'nightly'
        }

        r_result_1 = splunk.Client.validate_spec(spec_bad_ip)

        self.assertEqual(r_result_1, (False,
                         'Host {} not valid'.format(
                                            spec_bad_ip['hosts'][0])))

    def test__validate_spec_good(self):
        r_result_1 = splunk.Client.validate_spec(MULTI_SPEC)

        self.assertEqual(r_result_1, (True,
                         'It is valid!'))

    @patch.object(splunk, 'SplunkClient')
    def test__rotate_except(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        mk_splunk().change_passwd.side_effect = Exception('Boom!')
        cli._generate_splunk_passwd(32).return_value = "aaaabbbbcccc"

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPLUNK_SPEC)

    @patch.object(splunk, 'SplunkClient')
    def test__change_splunk_pass_except(self, mk_splunk):
        cli = splunk.Client(credentials=SPLUNK_CREDS, session=MagicMock(),
                            region_name='ap-southeast-2', verify=False)

        mk_splunk().change_passwd.side_effect = Exception('woot')

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
