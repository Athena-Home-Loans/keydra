import unittest
from keydra.clients.aws.secretsmanager import SecretsManagerClient
from keydra.clients.salesforce_marketing_cloud import SalesforceMarketingCloudClient

from keydra.providers import salesforce_marketing_cloud

from keydra.exceptions import ConfigException, DistributionException
from keydra.exceptions import RotationException

from unittest.mock import MagicMock
from unittest.mock import patch

SFMC_CREDS = {
    "provider": "salesforce_marketing_cloud",
    "key": "test@test.com",
    "secret": "test",
    "subdomain": "abc@_!xyz",
    "mid": 123456789,
    "businessUnit": 987654321,
}

SFMC_CFG = {
    'user_field': 'SF_USERNAME',
    'password_field': 'SF_PASSWORD',
    'subdomain_field': 'SF_SUBDOMAIN',
    'businessUnit_field': 'SF_BUSINESUNIT',
    'mid_field': 'SF_MID'
}

SFMC_SPEC = {
    'description': 'Test',
    'key': 'test@test.com',
    'provider': 'salesforce_marketing_cloud',
    'rotate': 'nightly',
    'distribute': [
        {
            'provider': 'secretsmanager',
            'source': 'secret',
            'key': 'keydra/salesforce/sfmc_test_api',
            'subdomain': 'abc@_!xyz',
            'mid': 123456789,
            'businessUnit': 987654321,
        },
        {
            'provider': 'bitbucket',
            'config': {'account_username': 'bla'},
            'scope': 'account',
            'source': 'secret',
            'key': 'keydra/salesforce/sfmc_test_api',
        }
    ]
}


class TestProviderSalesforce(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.cli = salesforce_marketing_cloud.Client(
            credentials=SFMC_CREDS,
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

    def test_init_missing_creds(self):
        with self.assertRaises(ConfigException):
            salesforce_marketing_cloud.Client()

    @patch.object(salesforce_marketing_cloud.Client, '_rotate_secret')
    def test_rotate(self, mk_rotate_secret):
        self.cli.rotate('something')
        mk_rotate_secret.assert_called_once_with('something')

    @patch.object(SecretsManagerClient, 'generate_random_password')
    @patch.object(SalesforceMarketingCloudClient, 'change_passwd')
    @patch.object(SalesforceMarketingCloudClient, '__init__')
    def test__rotate_secret_no_config(self, sfmc_init, sfmc_cp, sfmc_grp):
        sfmc_init.return_value = None
        new_pass = 'a' * 32
        sfmc_grp.return_value = new_pass

        # Act
        result = self.cli._rotate_secret(SFMC_SPEC)

        # Assert
        sfmc_cp.assert_called_once_with(
            username=SFMC_CREDS['key'],
            newpassword=new_pass
        )

        self.assertEqual(result['provider'], SFMC_CREDS['provider'])
        self.assertEqual(result['key'], SFMC_CREDS['key'])
        self.assertEqual(result['secret'], new_pass)
        self.assertEqual(result['subdomain'], SFMC_CREDS['subdomain'])
        self.assertEqual(result['mid'], SFMC_CREDS['mid'])
        self.assertEqual(result['businessUnit'], SFMC_CREDS['businessUnit'])

    @patch.object(SecretsManagerClient, 'generate_random_password')
    @patch.object(SalesforceMarketingCloudClient, 'change_passwd')
    @patch.object(SalesforceMarketingCloudClient, '__init__')
    def test__rotate_secret_overriden_fields(self, sfmc_init, sfmc_cp, smc_grp):
        orig_secret = {
            'SF_USERNAME': 'tester',
            'SF_PASSWORD': 'hide me',
            'SF_SUBDOMAIN': 'this is also secret',
            'SF_BUSINESUNIT': 123456789,
            'SF_MID': 987654321
        }
        self.cli = salesforce_marketing_cloud.Client(
            credentials=orig_secret,
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        sfmc_init.return_value = None
        new_pass = 'a' * 32
        smc_grp.return_value = new_pass

        # Act
        result = self.cli._rotate_secret({**SFMC_SPEC, 'config': SFMC_CFG})

        # Assert
        sfmc_cp.assert_called_once_with(
            username=orig_secret['SF_USERNAME'],
            newpassword=new_pass
        )

        self.assertEqual(result['SF_USERNAME'], orig_secret['SF_USERNAME'])
        self.assertEqual(result['SF_PASSWORD'], new_pass)
        self.assertEqual(result['SF_SUBDOMAIN'], orig_secret['SF_SUBDOMAIN'])
        self.assertEqual(result['SF_BUSINESUNIT'], orig_secret['SF_BUSINESUNIT'])
        self.assertEqual(result['SF_MID'], orig_secret['SF_MID'])

    @patch.object(SecretsManagerClient, 'generate_random_password')
    @patch.object(SalesforceMarketingCloudClient, 'change_passwd')
    @patch.object(SalesforceMarketingCloudClient, '__init__')
    def test__rotate_secret_rotate_excepts(self, sfmc_init, sfmc_cp, sfmc_gp):
        orig_secret = {
            'SF_USERNAME': 'tester',
            'SF_PASSWORD': 'hide me',
            'SF_SUBDOMAIN': 'this is also secret',
            'SF_BUSINESUNIT': 123456789,
            'SF_MID': 987654321
        }
        self.cli = salesforce_marketing_cloud.Client(
            credentials=orig_secret,
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        sfmc_init.return_value = None
        sfmc_cp.side_effect = Exception('Boom!')

        # Check Config exception
        with self.assertRaises(RotationException):
            self.cli._rotate_secret({**SFMC_SPEC, 'config': {}})

        # Check Password incorrect length exception
        with self.assertRaises(RotationException):
            self.cli._rotate_secret({**SFMC_SPEC, 'config': SFMC_CFG})

        # Check Try change password failure exception
        sfmc_gp.return_value = 'a' * 32
        with self.assertRaises(RotationException):
            self.cli._rotate_secret({**SFMC_SPEC, 'config': SFMC_CFG})

    def test__redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'salesforce_marketing_cloud',
                'key': 'KEY_ID',
                'secret': 'THIS_IS_SECRET',
                'subdomain': 'this is also secret',
                'mid': 'this is also secret',
                'businessUnit': 'this is also secret'
            }
        }

        r_result = salesforce_marketing_cloud.Client.redact_result(result, SFMC_CREDS)

        self.assertNotEqual(r_result['value']['secret'], 'THIS_IS_SECRET')
        self.assertNotEqual(r_result['value']['subdomain'], 'this is also secret')
        self.assertNotEqual(r_result['value']['mid'], 'this is also secret')
        self.assertNotEqual(r_result['value']['businessUnit'], 'this is also secret')

    def test__redact_result_overriden_fields(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'SF_USERNAME': 'tester',
                'SF_PASSWORD': 'hide me',
                'SF_SUBDOMAIN': 'this is also secret',
                'SF_BUSINESUNIT': 'test',
                'SF_MID': 'test'
            }
        }

        redacted = salesforce_marketing_cloud.Client.redact_result(
            result,
            {**SFMC_CREDS, 'config': SFMC_CFG}
        )

        self.assertEqual(redacted['value']['SF_USERNAME'], 'tester')
        self.assertEqual(redacted['value']['SF_PASSWORD'], '***')
        self.assertEqual(redacted['value']['SF_SUBDOMAIN'], '***')
        self.assertEqual(redacted['value']['SF_BUSINESUNIT'], '***')
        self.assertEqual(redacted['value']['SF_MID'], '***')

    def test__redact_result_no_secrets(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = salesforce_marketing_cloud.Client.redact_result(result, SFMC_CREDS)

        self.assertEqual(r_result, result)

    def test__validate_spec_no_config(self):
        r_result_1 = salesforce_marketing_cloud.Client.validate_spec(SFMC_SPEC)

        self.assertEqual(r_result_1, (True, 'It is valid!'))

    def test__validate_invalid_spec_no_config(self):
        r_result_1 = salesforce_marketing_cloud.Client.validate_spec({'desc': 'test'})

        self.assertEqual(
            r_result_1,
            (False, 'Invalid spec. Missing keys: provider, key for {\n  "desc": "test"\n}')
        )

    def test__validate_spec_known_config_fields(self):
        result = salesforce_marketing_cloud.Client.validate_spec({**SFMC_SPEC, 'config': SFMC_CFG})

        self.assertEqual(result, (True, 'It is valid!'))

    def test__validate_spec_unknown_config_fields(self):
        result = salesforce_marketing_cloud.Client.validate_spec(
            {**SFMC_SPEC, 'config': {'MID': 'a', 'm1d': 'b'}})

        self.assertEqual(result, (False, 'Unknown config fields: MID, m1d'))

    def test__distribute_exception(self):
        with self.assertRaises(DistributionException):
            self.cli.distribute(secret='secret', destination='dest')

    @patch.object(SecretsManagerClient, 'generate_random_password')
    def test__generate_sfmc_pass(self, sfmc_cp):
        sfmc_cp.return_value = 'Bj*7QEb2RoWUqYM!@92o87g5LdP#$Cy*'
        pw_result = self.cli._generate_sfmc_passwd(32)

        self.assertEqual(32, len(pw_result))
        self.assertEqual(pw_result, 'Bj*7QEb2RoWUqYM!@92o87g5LdP#$Cy*')

    @patch('keydra.providers.salesforce_marketing_cloud.boto3')
    def test__boto_none(self, mk_boto):
        salesforce_marketing_cloud.Client(
            credentials=SFMC_CREDS,
            session=None,
            region_name='ap-southeast-2'
        )
        mk_boto.session.Session.assert_called_once_with()
