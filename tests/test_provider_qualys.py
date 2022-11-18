import unittest
import json

from keydra.providers import qualys

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from unittest.mock import MagicMock
from unittest.mock import patch

CREDS = {
  "platform": "US3",
  "username": "user",
  "password": "pass",
}

OP_CREDS = {
  "platform": "US3",
  "username": "user2",
  "password": "pass2",
}

SPEC = {
    'description': 'Test',
    'key': 'secretone',
    'provider': 'qualys',
    'rotate': 'nightly',
    'config': {
        'rotatewith': {
            'key': 'keydra/qualys/secrettwo',
            'provider': 'secretsmanager'
        }
    }
}


class TestProviderQualys(unittest.TestCase):
    @patch.object(qualys, 'loader')
    @patch.object(qualys, 'json')
    @patch.object(qualys, 'QualysClient')
    def test_rotate(self, mk_qualys, mk_json, mk_ldr):
        mk_json.loads.return_value = OP_CREDS

        cli = qualys.Client(credentials=CREDS, session=MagicMock(),
                            region_name='ap-southeast-2')

        mk_ldr.fetch_provider_creds.return_value = json.dumps(OP_CREDS)

        result = cli._rotate_secret(SPEC)

        self.assertEqual(type(result), dict)
        self.assertEqual(
            result['password']._extract_mock_name(),
            'QualysClient().change_passwd()'
        )

    @patch.object(qualys, 'loader')
    @patch.object(qualys, 'json')
    @patch.object(qualys, 'QualysClient')
    def test_rotate_nocreds(self, mk_qualys, mk_json, mk_ldr):
        mk_json.loads.return_value = OP_CREDS

        cli = qualys.Client(credentials=None, session=MagicMock(),
                            region_name='ap-southeast-2')

        mk_ldr.fetch_provider_creds.return_value = json.dumps(OP_CREDS)

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPEC)

    @patch.object(qualys, 'loader')
    @patch.object(qualys, 'json')
    @patch.object(qualys, 'QualysClient')
    def test_init_nosess(self, mk_qualys, mk_json, mk_ldr):
        mk_json.loads.return_value = OP_CREDS

        cli = qualys.Client(credentials=CREDS, region_name='ap-southeast-2')

        self.assertEqual(type(cli), qualys.Client)

    @patch.object(qualys, 'loader')
    @patch.object(qualys, 'json')
    @patch.object(qualys, 'QualysClient')
    def test_distribute(self, mk_qualys, mk_json, mk_ldr):
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
                'provider': 'qualys',
                'username': 'SOME_USERNAME',
                'password': 'THIS_IS_SECRET'
            }
        }

        r_result = qualys.Client.redact_result(result, {})

        self.assertEqual(r_result['value']['provider'], 'qualys')
        self.assertEqual(r_result['value']['username'], 'SOME_USERNAME')
        self.assertEqual(r_result['value']['password'], '***')

    def test__redact_result_no_secret(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = qualys.Client.redact_result(result, {})

        self.assertEqual(r_result, result)

    def test__validate_spec_good(self):
        r_result_1 = qualys.Client.validate_spec(SPEC)

        self.assertEqual(r_result_1, (True,
                         'It is valid!'))

    @patch.object(qualys, 'loader')
    @patch.object(qualys, 'json')
    @patch.object(qualys, 'QualysClient')
    def test__rotate_except(self, mk_qualys, mk_json, mk_ldr):
        cli = qualys.Client(credentials=CREDS, session=MagicMock(),
                            region_name='ap-southeast-2')

        mk_ldr.fetch_provider_creds.return_value = json.dumps(OP_CREDS)

        mk_qualys().change_passwd.side_effect = Exception('Boom!')

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPEC)

    @patch.object(qualys, 'loader')
    @patch.object(qualys, 'json')
    @patch.object(qualys, 'QualysClient')
    def test__change_pass_except(self, mk_qualys, mk_json, mk_ldr):
        cli = qualys.Client(credentials=CREDS, session=MagicMock(),
                            region_name='ap-southeast-2')

        mk_qualys().change_passwd.side_effect = Exception('woot')

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPEC)

    def test_validate_spec_fail(self):
        spec_no_cfg = {
            'description': 'Test',
            'key': 'secretone',
            'provider': 'qualys',
            'rotate': 'nightly',
            'config': {
                'rotatewith': {
                    'key': 'keydra/qualys/secrettwo'
                }
            }
        }

        r_result = qualys.Client.validate_spec(spec_no_cfg)
        self.assertEqual(r_result, (False,
                         '"config" stanza must include keys key, provider'))

    def test_validate_spec_fail2(self):
        spec_no_key = {
            'description': 'Test',
            'provider': 'qualys',
            'rotate': 'nightly',
            'config': {
                'rotatewith': {
                    'key': 'keydra/qualys/secrettwo'
                }
            }
        }

        r_result, r_msg = qualys.Client.validate_spec(spec_no_key)

        self.assertEqual(r_result, False)
        self.assertEqual(r_msg.startswith('Invalid spec. Missing keys'), True)
