import unittest
import json

from keydra.providers import salesforce

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from unittest.mock import MagicMock
from unittest.mock import patch

SF_CREDS = {
    "provider": "salesforce",
    "key": "test@test.com",
    "secret": "test",
    "token": "token",
    "env": "dev11",
    "domain": "test"
}

SF_SPEC = {
    'description': 'Test',
    'key': 'splunk',
    'provider': 'salesforce',
    'rotate': 'nightly',
    'distribute': [
        {
            'provider': 'secretsmanager',
            'source': 'secret',
            'key': 'keydra/salesforce/splunk',
            'envs': ['dev']
        },
        {
            'provider': 'bitbucket',
            'config': {'account_username': 'bla'},
            'scope': 'account',
            'source': 'secret',
            'key': 'keydra/salesforce/splunk',
            'envs': ['dev']
        }
    ]
}


class TestProviderSalesforce(unittest.TestCase):

    @patch.object(salesforce, 'SalesforceClient')
    @patch.object(salesforce.Client, '_rotate_secret')
    def test_rotate(self, mk_rotate_secret, mk_sf_client):
        cli = salesforce.Client(credentials=SF_CREDS, session=MagicMock(),
                                region_name='ap-southeast-2')

        cli.rotate('something')

        mk_rotate_secret.assert_called_once_with('something')

    def test__redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'splunk',
                'key': 'KEY_ID',
                'secret': 'THIS_IS_SECRET',
                'token': 'this is also secret'
            }
        }

        r_result = salesforce.Client.redact_result(result)
        r_secret = r_result['value']['secret']
        r_token = r_result['value']['token']

        self.assertNotEqual(r_secret, 'THIS_IS_SECRET')
        self.assertNotEqual(r_token, 'this is also secret')

    def test__redact_result_no_secrets(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = salesforce.Client.redact_result(result)

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
            'key': 'splunk',
            'provider': 'salesforce',
            'rotate': 'nightly'
        }

        r_result = salesforce.Client.validate_spec(spec_overlength)
        self.assertEqual(r_result, (False,
                         'Value for key description failed length checks'))

    def test_validate_spec_underlength(self):
        spec_underlength = {
            'e': 'e',
            'key': 'splunk',
            'provider': 'salesforce',
            'rotate': 'nightly'
        }

        r_result = salesforce.Client.validate_spec(spec_underlength)
        self.assertEqual(r_result, (False, 'Key e failed length checks'))

    def test_validate_spec_underlength_nested(self):
        spec_underlength = {
            'ewewewe': 'eewewew',
            'key': 'splunk',
            'provider': 'salesforce',
            'rotate': ['nightly', 'e']
        }

        r_result = salesforce.Client.validate_spec(spec_underlength)
        self.assertEqual(r_result, (False, 'List entry failed length checks'))

    def test_validate_spec_overlength_nested(self):
        spec_overlength = {
            'description': ['Lorem ipsum dolor sit amet, '
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
                            'id est laborum.'],
            'key': 'splunk',
            'provider': 'salesforce',
            'rotate': 'nightly'
        }

        r_result = salesforce.Client.validate_spec(spec_overlength)
        self.assertEqual(r_result, (False,
                         'List entry failed length checks'))

    def test_validate_underlength_dict_nested(self):
        spec_underlength = {
            'description': 'Test',
            'key': 'splunk',
            'provider': 'salesforce',
            'rotate': 'nightly',
            'distribute': [
                {
                    'e': 'secretsmanager',
                    'source': 'secret',
                    'key': 'keydra/salesforce/splunk',
                    'envs': ['dev'],
                    'provider': 'salesforce',
                }
            ]
        }

        r_result = salesforce.Client.validate_spec(spec_underlength)
        self.assertEqual(r_result, (False, 'Dict entry failed length checks'))

    def test_validate_overlength_dict_nested(self):
        spec_overlength = {
            'description': [
                {
                    'key': 'Lorem ipsum dolor sit, '
                    'consectetur adipiscing elit, '
                    'sed do eiusmod tempor incididunt'
                    'ut labore et dolore magna'
                    'aliqua. Ut enim ad minim veniam,'
                    'quis nostrud exercitation'
                    ' ullamco laboris nisi ut aliquip'
                    'ex ea commodo consequat. '
                    'Duis aute irure dolor in reprehenderit'
                    'in voluptate velit esse cillumlore eu'
                    'fugiat nulla pariatur. Excepteur sint'
                    ' occaecat cupidatat non proident, sunt in'
                    'culpa qui officia deserunt mollit anim '
                    'id est laborum.',
                    'provider': 'salesforce'
                }
            ],
            'key': 'splunk',
            'provider': 'salesforce',
            'rotate': 'nightly'
        }

        r_result = salesforce.Client.validate_spec(spec_overlength)
        self.assertEqual(r_result, (False,
                         'Dict entry failed length checks'))

    def test__validate_spec_good(self):
        r_result_1 = salesforce.Client.validate_spec(SF_SPEC)

        self.assertEqual(r_result_1, (True,
                         'It is valid!'))

    @patch.object(salesforce, 'SalesforceClient')
    def test__distribute_exception(self, mk_sf_client):
        cli = salesforce.Client(credentials=SF_CREDS, session=MagicMock(),
                                region_name='ap-southeast-2')

        with self.assertRaises(DistributionException):
            cli.distribute(secret='secret', destination='dest')

    @patch.object(salesforce, 'SalesforceClient')
    def test__sm_creds_except(self, mk_sforce):
        cli = salesforce.Client(
            credentials=SF_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.side_effect = Exception('Boom!')

        with self.assertRaises(RotationException):
            cli._rotate_secret(secret=SF_CREDS)

    @patch.object(salesforce, 'SalesforceClient')
    def test__gen_pass_good(self, mk_sforce):
        cli = salesforce.Client(
            credentials=SF_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SF_CREDS)
        cli._generate_sforce_passwd = MagicMock()
        new_pass = "12345678901234567890123456789012"
        cli._generate_sforce_passwd.return_value = new_pass

        r_result = cli._rotate_secret(secret=SF_CREDS)

        cli._generate_sforce_passwd.assert_called_once_with(32)
        self.assertEqual(r_result['secret'], new_pass)

    @patch.object(salesforce, 'SalesforceClient')
    def test__gen_pass_bad(self, mk_sforce):
        cli = salesforce.Client(
            credentials=SF_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SF_CREDS)
        cli._generate_sforce_passwd = MagicMock()
        cli._generate_sforce_passwd.return_value = "123456789012123456789012"

        with self.assertRaises(RotationException):
            cli._rotate_secret(secret=SF_CREDS)

    @patch.object(salesforce, 'SalesforceClient')
    def test__sforce_pass_change_except(self, mk_sforce):
        cli = salesforce.Client(
            credentials=SF_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SF_CREDS)
        cli._generate_sforce_passwd = MagicMock()
        new_pass = "12345678901234567890123456789012"
        cli._generate_sforce_passwd.return_value = new_pass

        mk_sforce._init.side_effect = Exception

        mk_sforce().change_passwd.side_effect = Exception('Boom')

        with self.assertRaises(RotationException):
            cli._rotate_secret(secret=SF_CREDS)

    @patch.object(salesforce, 'SalesforceClient')
    def test__sm_pass_gen(self, mk_sforce):
        cli = salesforce.Client(
            credentials=SF_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        cli._smclient = MagicMock()
        cli._smclient.get_secret_value.return_value = json.dumps(SF_CREDS)
        cli._smclient.generate_random_password = MagicMock()
        new_pass = "12345678901234567890123456789012"
        cli._smclient.generate_random_password.return_value = new_pass

        mk_sforce._init.side_effect = Exception

        cli._rotate_secret(secret=SF_CREDS)

        cli._smclient.generate_random_password.assert_called_once_with(
            IncludeSpace=True,
            length=32,
            ExcludeCharacters='!"%&\'()*+,-./:;<=>?[\\]^_`{|}~$'
        )

    @patch.object(salesforce, 'SalesforceClient')
    @patch('keydra.providers.salesforce.boto3')
    def test__boto_none(self, mk_boto, mk_sf_client):
        salesforce.Client(
            credentials=SF_CREDS,
            session=None,
            region_name='ap-southeast-2'
        )
        mk_boto.session.Session.assert_called_once_with()
