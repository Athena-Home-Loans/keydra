import unittest

from keydra.providers import splunk_hec

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from unittest.mock import MagicMock
from unittest.mock import patch

from keydra.providers.splunk_hec import PW_FIELD

SPLUNK_CREDS = {
    "username": "admin_key",
    "password": "test"
}

SPLUNK_HECSPEC = {
    'description': 'Test',
    'key': 'keydra/splunk',
    'config': {
        'host': '127.0.0.1',
        'type': 'hectoken',
        'rotatewith': {
            'key': 'blah',
            'provider': 'secretsmanager'
        }
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


class TestProviderSplunkHEC(unittest.TestCase):
    @patch('json.loads')
    @patch.object(splunk_hec, 'SplunkClient')
    def test__rotate_hec(self,  mk_splunk, mk_loads):
        cli = splunk_hec.Client(
            credentials=SPLUNK_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2',
            verify=False
        )
        mk_loads.return_value = {'key': 'test', 'secret': 'sshhh'}
        cli._rotate_secret(SPLUNK_HECSPEC)

        self.assertEqual(mk_splunk().rotate_hectoken.call_count, 1)

    @patch('json.loads')
    @patch.object(splunk_hec, 'SplunkClient')
    def test__rotate_hec_fail(self,  mk_splunk, mk_loads):
        cli = splunk_hec.Client(
            credentials=SPLUNK_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2',
            verify=False
        )

        mk_splunk().rotate_hectoken.side_effect = Exception('boom')
        mk_loads.return_value = {'key': 'test', 'secret': 'sshhh'}

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPLUNK_HECSPEC)

    @patch.object(splunk_hec.Client, '_rotate_secret')
    def test_rotate(self, mk_rotate_secret):
        cli = splunk_hec.Client(
            credentials=SPLUNK_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2',
            verify=False
        )

        cli.rotate('something')

        mk_rotate_secret.assert_called_once_with('something')

    def test__redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'splunk',
                'key': 'KEY_ID',
                f'{PW_FIELD}': 'THIS_IS_SECRET'
            }
        }

        r_result = splunk_hec.Client.redact_result(result)
        r_value = r_result['value'][PW_FIELD]

        self.assertNotEqual(r_value, 'THIS_IS_SECRET')

    def test__redact_result_no_secret(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = splunk_hec.Client.redact_result(result)

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

        r_result = splunk_hec.Client.validate_spec(spec_bad_domain)

        self.assertEqual(
            r_result,
            (
                False,
                'Host {} must be a valid IP or domain name'.format(
                    spec_bad_domain['config']['host']
                )
            )
        )

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

        r_result_1 = splunk_hec.Client.validate_spec(spec_bad_ip)

        self.assertEqual(
            r_result_1,
            (
                False,
                'Host {} must be a valid IP or domain name'.format(
                    spec_bad_ip['config']['host']
                )
            )
        )

    def test_validate_hec(self):
        r_result_hec = splunk_hec.Client.validate_spec(SPLUNK_HECSPEC)

        self.assertEqual(r_result_hec, (True, 'It is valid!'))

    def test__distribute(self):
        cli = splunk_hec.Client(
            credentials=SPLUNK_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2',
            verify=False
        )

        with self.assertRaises(DistributionException):
            cli.distribute(secret=SF_CREDS, destination=DEST)
