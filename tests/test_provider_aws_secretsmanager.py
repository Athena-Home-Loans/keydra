import json
import unittest

from unittest.mock import MagicMock
from unittest.mock import patch

from keydra.exceptions import DistributionException, RotationException

from keydra.clients.aws.secretsmanager import GetSecretException
from keydra.clients.aws.secretsmanager import UpdateSecretException
from keydra.providers.aws_secretsmanager import SecretsManagerProvider


IAM_SECRET = {
    'key': 'secret_key',
    'secret': 'secret_secret',
    'provider': 'iam'
}

SM_DEST = {
    'key': 'secret_name',
    'provider': 'secretsmanager'
}


class TestProviderAWSSecretsManager(unittest.TestCase):
    def test__distribute_secret_new_key(self):
        cli = SecretsManagerProvider(session=MagicMock())

        cli._client = MagicMock()
        cli._client.describe_secret.side_effect = GetSecretException

        cli._distribute_secret(IAM_SECRET, SM_DEST)

        cli._client.describe_secret.assert_called_once_with(
            secret_id=SM_DEST['key']
        )
        cli._client.create_secret.assert_called_once_with(
            secret_name=SM_DEST['key'],
            secret_value=json.dumps(IAM_SECRET),
            description='Keydra managed secret {}'.format(SM_DEST['key'])
        )
        cli._client.update_secret.assert_not_called()

    def test__distribute_secret_existing_key(self):
        cli = SecretsManagerProvider(session=MagicMock())

        cli._client = MagicMock()
        cli._client.describe_secret.return_value = 'stuff'

        cli._distribute_secret(IAM_SECRET, SM_DEST)

        cli._client.describe_secret.assert_called_once_with(
            secret_id=SM_DEST['key']
        )
        cli._client.update_secret.assert_called_once_with(
            secret_id=SM_DEST['key'],
            secret_value=json.dumps(IAM_SECRET),
        )
        cli._client.create_secret.assert_not_called()

    def test__raise_on_failed_update(self):
        cli = SecretsManagerProvider(session=MagicMock())

        cli._client = MagicMock()
        cli._client.describe_secret.return_value = 'stuff'
        cli._client.update_secret.side_effect = UpdateSecretException

        with self.assertRaises(DistributionException):
            cli._distribute_secret(IAM_SECRET, SM_DEST)

    def test_distribute(self):
        cli = SecretsManagerProvider(session=MagicMock())

        with patch.object(cli, '_distribute_secret') as mk_ds:
            cli.distribute(IAM_SECRET, SM_DEST)

            mk_ds.assert_called_once_with(IAM_SECRET, SM_DEST)

    def test_rotate_no_bypass(self):
        # Arrange
        cli = SecretsManagerProvider(session=MagicMock(), client=MagicMock())
        cli._client.get_secret_value.return_value = json.dumps({
            'a': 'not-rotated', 'the_secret_attribute': 'old-val'})
        cli._client.generate_random_password.return_value = 'new-val'

        spec = {
            'key': 'secret_name',
            'provider': 'secretsmanager',
            'config': SecretsManagerProvider.Options(
                rotate_attribute='the_secret_attribute')._asdict()
        }

        # Act
        return_val = cli.rotate(spec)

        # Assert
        self.assertEqual(return_val, {
            'a': 'not-rotated',
            'the_secret_attribute': 'new-val',
            'provider': 'secretsmanager'})

        cli._client.get_secret_value.assert_called_once_with(spec['key'])
        cli._client.generate_random_password.assert_called_once_with(
            length=32,
            ExcludeCharacters='',
            ExcludeNumbers=False,
            ExcludePunctuation=False,
            ExcludeUppercase=False,
            ExcludeLowercase=False,
            IncludeSpace=False,
            RequireEachIncludedType=True,
        )

        cli._client.update_secret.assert_called_once_with(
            spec['key'],
            json.dumps(return_val),
        )

    def test_rotate_cant_get_current(self):
        cli = SecretsManagerProvider(session=MagicMock(), client=MagicMock())
        cli._client.get_secret_value.side_effect = GetSecretException

        spec = {
            'key': 'secret_name',
            'provider': 'secretsmanager',
            'config': SecretsManagerProvider.Options(
                rotate_attribute='the_secret_attribute')._asdict()
        }

        with self.assertRaises(RotationException):
            cli.rotate(spec)

        cli._client.get_secret_value.assert_called_once_with(spec['key'])

    def test_rotate_no_bypass_override_generated_pass_options(self):
        # Arrange
        cli = SecretsManagerProvider(session=MagicMock(), client=MagicMock())
        cli._client.get_secret_value.return_value = json.dumps({
            'a': 'not-rotated', 'the_secret_attribute': 'old-val'})
        cli._client.generate_random_password.return_value = 'new-val'

        spec = {
            'key': 'secret_name',
            'provider': 'secretsmanager',
            'config': SecretsManagerProvider.Options(
                rotate_attribute='the_secret_attribute',
                exclude_char='abc',
                exclude_lower=True,
                exclude_upper=True,
                exclude_num=True,
                exclude_punct=True,
                include_space=True,
                length=12,
                require_each_type=False
            )._asdict()
        }

        # Act
        return_val = cli.rotate(spec)

        # Assert
        cli._client.generate_random_password.assert_called_once_with(
            length=12,
            ExcludeCharacters='abc',
            ExcludeNumbers=True,
            ExcludePunctuation=True,
            ExcludeUppercase=True,
            ExcludeLowercase=True,
            IncludeSpace=True,
            RequireEachIncludedType=False,
        )

        cli._client.update_secret.assert_called_once_with(
            spec['key'],
            json.dumps(return_val),
        )

    def test_rotate_with_bypass(self):
        cli = SecretsManagerProvider(session=MagicMock())
        cli._client = MagicMock()
        cli._client.get_secret_value.return_value = json.dumps({
            'key1': 'val1'
        })

        result = cli.rotate({
            'key': 'secret_name',
            'provider': 'secretsmanager',
            'config': {
                'bypass': True
            }
        })

        self.assertEqual(result, {
            'key1': 'val1',
            'provider': 'secretsmanager'
        })
        cli._client.get_secret_value.assert_called_once_with('secret_name')

    def test_validate_spec_base_fail(self):
        speci_valid = {
            'missing-provider': 'bananas',
            'key': 'abc'
        }

        r_result = SecretsManagerProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)

    def test_validate_spec_no_config(self):
        speci_valid = {
            'provider': 'secretsmanager',
            'key': 'abc'
        }

        r_result = SecretsManagerProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)

    def test_validate_spec_has_bypass_and_attr_name(self):
        speci_valid = {
            'provider': 'secretsmanager',
            'key': 'abc',
            'config': SecretsManagerProvider.Options(
                bypass=True,
                rotate_attribute='my_pass'
            )._asdict()
        }

        r_result = SecretsManagerProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)

    def test_validate_spec_with_source(self):
        speci_valid = {
            'provider': 'secretsmanager',
            'key': 'abc',
            'source': 'bananas'
        }

        r_result = SecretsManagerProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], True)

    def test_validate_spec_with_rotate_attribute(self):
        speci_valid = {
            'provider': 'secretsmanager',
            'key': 'abc',
            'config': {
                'rotate_attribute': 'my_pass',
                'length': 123
            }
        }

        r_result = SecretsManagerProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], True)

    def test_redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'cloudflare',
                'a': '1',
                'b': '2'
            }
        }

        r_result = SecretsManagerProvider.redact_result(result, {})

        self.assertEqual(r_result, {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'cloudflare',
                'a': '***',
                'b': '***'
            }
        })
