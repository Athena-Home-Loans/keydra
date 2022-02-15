import unittest
import json
from keydra.clients.aws.secretsmanager import SecretsManagerClient
from keydra.clients.salesforce import SalesforceClient

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

    @patch.object(SecretsManagerClient, 'generate_random_password')
    @patch.object(SalesforceClient, 'change_passwd')
    @patch.object(SalesforceClient, 'get_user_id')
    @patch.object(SalesforceClient, '__init__')
    def test__rotate_secret_no_config(self, sf_init, sf_gui, sf_cp, smc_grp):
        # Arrange
        cli = salesforce.Client(credentials=SF_CREDS,
                                session=MagicMock(),
                                region_name='ap-southeast-2')

        sf_init.return_value = None
        new_pass = 'a' * 32
        smc_grp.return_value = new_pass
        sf_gui.return_value = 'user'

        # Act
        result = cli._rotate_secret(SF_SPEC)

        # Assert
        sf_cp.assert_called_once_with(
            userid='user',
            newpassword=new_pass
        )

        self.assertEqual(result['provider'], SF_CREDS['provider'])
        self.assertEqual(result['key'], SF_CREDS['key'])
        self.assertEqual(result['secret'], new_pass)
        self.assertEqual(result['token'], SF_CREDS['token'])
        self.assertEqual(result['env'], SF_CREDS['env'])
        self.assertEqual(result['domain'], SF_CREDS['domain'])

    @patch.object(SecretsManagerClient, 'generate_random_password')
    @patch.object(SalesforceClient, 'change_passwd')
    @patch.object(SalesforceClient, 'get_user_id')
    @patch.object(SalesforceClient, '__init__')
    def test__rotate_secret_overridden_fields(
            self, sf_init, sf_gui, sf_cp, smc_grp):
        # Arrange
        cfg = {
            'user_field': 'SF_USERNAME',
            'password_field': 'SF_PASSWORD',
            'token_field': 'SF_TOKEN',
            'domain_field': 'SF_DOMAIN',
        }
        orig_secret = {
            'SF_USERNAME': 'tester',
            'SF_PASSWORD': 'hide me',
            'SF_TOKEN': 'this is also secret',
            'SF_DOMAIN': 'test',
            'env': 'test',
        }
        cli = salesforce.Client(credentials=orig_secret,
                                session=MagicMock(),
                                region_name='ap-southeast-2')

        sf_init.return_value = None
        new_pass = 'a' * 32
        smc_grp.return_value = new_pass
        sf_gui.return_value = 'user'

        # Act
        result = cli._rotate_secret({**SF_SPEC, 'config': cfg})

        # Assert
        sf_cp.assert_called_once_with(
            userid='user',
            newpassword=new_pass
        )

        self.assertEqual(result['SF_USERNAME'], orig_secret['SF_USERNAME'])
        self.assertEqual(result['SF_TOKEN'], orig_secret['SF_TOKEN'])
        self.assertEqual(result['SF_PASSWORD'], new_pass)
        self.assertEqual(result['SF_DOMAIN'], orig_secret['SF_DOMAIN'])
        self.assertEqual(result['env'], orig_secret['env'])

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

        r_result = salesforce.Client.redact_result(result, SF_CREDS)
        r_secret = r_result['value']['secret']
        r_token = r_result['value']['token']

        self.assertNotEqual(r_secret, 'THIS_IS_SECRET')
        self.assertNotEqual(r_token, 'this is also secret')

    def test__redact_result_overriden_fields(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'SF_USERNAME': 'tester',
                'SF_PASSWORD': 'hide me',
                'SF_TOKEN': 'this is also secret',
                'SF_DOMAIN': 'test',
            }
        }

        redacted = salesforce.Client.redact_result(result, {**SF_CREDS, 'config': {
            'user_field': 'SF_USERNAME',
            'password_field': 'SF_PASSWORD',
            'token_field': 'SF_TOKEN',
            'domain_field': 'SF_DOMAIN',
        }})

        self.assertEqual(redacted['value']['SF_USERNAME'], 'tester')
        self.assertEqual(redacted['value']['SF_PASSWORD'], '***')
        self.assertEqual(redacted['value']['SF_TOKEN'], '***')
        self.assertEqual(redacted['value']['SF_DOMAIN'], 'test')

    def test__redact_result_no_secrets(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = salesforce.Client.redact_result(result, SF_CREDS)

        self.assertEqual(r_result, result)

    def test__validate_spec_no_config(self):
        r_result_1 = salesforce.Client.validate_spec(SF_SPEC)

        self.assertEqual(r_result_1, (True,
                         'It is valid!'))

    def test__validate_spec_known_config_fields(self):
        result = salesforce.Client.validate_spec(
            {**SF_SPEC, 'config': {
                'user_field': 'user',
                'password_field': 'pass',
                'token_field': 'SF_TOKEN',
                'domain_field': 'DOMAIN',
            }})

        self.assertEqual(result, (True,
                         'It is valid!'))

    def test__validate_spec_unknown_config_fields(self):
        result = salesforce.Client.validate_spec(
            {**SF_SPEC, 'config': {'field1': 'a', 'field2': 'b'}})

        self.assertEqual(result, (False,
                         'Unknown config fields: field1, field2'))

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
            cli._rotate_secret(spec=SF_CREDS)

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

        r_result = cli._rotate_secret(spec=SF_CREDS)

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
            cli._rotate_secret(spec=SF_CREDS)

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
            cli._rotate_secret(spec=SF_CREDS)

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

        cli._rotate_secret(spec=SF_CREDS)

        cli._smclient.generate_random_password.assert_called_once_with(
            IncludeSpace=False,
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
