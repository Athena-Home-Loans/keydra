import unittest

from keydra.providers import qualys

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from unittest.mock import MagicMock
from unittest.mock import patch

CREDS = {
  "platform": "US3",
  "username": "user",
  "password": "pass",
  "rotatewith": "secrettwo"
}

OP_CREDS = {
  "platform": "US3",
  "username": "user2",
  "password": "pass2",
  "rotatewith": "secretone"
}

SPEC = {
    'description': 'Test',
    'key': 'secretone',
    'provider': 'splunk',
    'rotate': 'nightly'
}


class TestProviderSplunk(unittest.TestCase):
    @patch.object(qualys, 'json')
    @patch.object(qualys, 'SecretsManagerClient')
    @patch.object(qualys, 'QualysClient')
    def test_rotate(self, mk_qualys, mk_sm, mk_json):
        mk_json.loads.return_value = OP_CREDS

        cli = qualys.Client(credentials=CREDS, session=MagicMock(),
                            region_name='ap-southeast-2')

        result = cli.rotate('something')

        self.assertEqual(type(result), dict)
        self.assertEqual(
            result['password']._extract_mock_name(),
            'QualysClient().change_passwd()'
        )

    @patch.object(qualys, 'json')
    @patch.object(qualys, 'SecretsManagerClient')
    @patch.object(qualys, 'QualysClient')
    def test_distribute(self, mk_qualys, mk_sm, mk_json):
        mk_json.loads.return_value = OP_CREDS

        cli = qualys.Client(credentials=CREDS, session=MagicMock(),
                            region_name='ap-southeast-2')

        with self.assertRaises(DistributionException):
            cli.distribute(secret='secret', destination='dest')

    def test__redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'splunk',
                'key': 'KEY_ID',
                'password': 'THIS_IS_SECRET'
            }
        }

        r_result = qualys.Client.redact_result(result)
        r_value = r_result['value']['password']

        self.assertNotEqual(r_value, 'THIS_IS_SECRET')

    def test__redact_result_no_secret(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = qualys.Client.redact_result(result)

        self.assertEqual(r_result, result)

    def test__validate_spec_good(self):
        r_result_1 = qualys.Client.validate_spec(SPEC)

        self.assertEqual(r_result_1, (True,
                         'It is valid!'))

    @patch.object(qualys, 'json')
    @patch.object(qualys, 'SecretsManagerClient')
    @patch.object(qualys, 'QualysClient')
    def test__rotate_except(self, mk_qualys, mk_sm, mk_json):
        cli = qualys.Client(credentials=CREDS, session=MagicMock(),
                            region_name='ap-southeast-2')

        mk_qualys().change_passwd.side_effect = Exception('Boom!')

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPEC)

    @patch.object(qualys, 'json')
    @patch.object(qualys, 'SecretsManagerClient')
    @patch.object(qualys, 'QualysClient')
    def test__change_pass_except(self, mk_qualys, mk_sm, mk_json):
        cli = qualys.Client(credentials=CREDS, session=MagicMock(),
                            region_name='ap-southeast-2')

        mk_qualys().change_passwd.side_effect = Exception('woot')

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPEC)

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
            'key': 'test',
            'provider': 'qualys',
            'rotate': 'nightly'
        }

        r_result = qualys.Client.validate_spec(spec_overlength)
        self.assertEqual(r_result, (False,
                         'Value for key description failed length checks'))
