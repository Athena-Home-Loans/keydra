import json
import unittest

from unittest.mock import MagicMock
from unittest.mock import patch

from keydra.exceptions import DistributionException, RotationException

from keydra.clients.aws.ssmparameterstore import PutParameterException, GetParameterException
from keydra.providers.aws_ssmparameterstore import SSMParameterProvider

IAM_SECRET = {
    'key': 'secret_key',
    'secret': 'secret_secret',
    'provider': 'iam'
}

SSM_DEST = {
    'key': 'secret_name',
    'provider': 'ssmparameterstore'
}


class TestProviderAWSSSMParameterStore(unittest.TestCase):
    def test__distribute_secret_new_key(self):
        cli = SSMParameterProvider(session=MagicMock())

        cli._client = MagicMock()
        cli._client.parameter_exists.return_value = False

        cli._distribute_secret(IAM_SECRET, SSM_DEST)

        cli._client.parameter_exists.assert_called_once_with(
            SSM_DEST['key']
        )
        cli._client.put_parameter_securestring.assert_called_once_with(
            param_name=SSM_DEST['key'],
            param_value=json.dumps(IAM_SECRET),
            description='Keydra managed secret {}'.format(SSM_DEST['key'])
        )

    def test__distribute_secret_existing_key(self):
        cli = SSMParameterProvider(session=MagicMock())

        cli._client = MagicMock()
        cli._client.parameter_exists.return_value = True

        cli._distribute_secret(IAM_SECRET, SSM_DEST)

        cli._client.parameter_exists.assert_called_once_with(
            SSM_DEST['key']
        )
        cli._client.put_parameter_securestring.assert_called_once_with(
            param_name=SSM_DEST['key'],
            param_value=json.dumps(IAM_SECRET),
            description='Keydra managed secret {}'.format(SSM_DEST['key'])
        )

    def test__raise_on_failed_update(self):
        cli = SSMParameterProvider(session=MagicMock())

        cli._client = MagicMock()
        cli._client.parameter_exists.return_value = True
        cli._client.put_parameter_securestring.side_effect = PutParameterException

        with self.assertRaises(DistributionException):
            cli._distribute_secret(IAM_SECRET, SSM_DEST)

    def test_distribute(self):
        cli = SSMParameterProvider(session=MagicMock())

        with patch.object(cli, '_distribute_secret') as mk_ds:
            cli.distribute(IAM_SECRET, SSM_DEST)

            mk_ds.assert_called_once_with(IAM_SECRET, SSM_DEST)

    def test_rotate_no_bypass(self):
        # Arrange
        cli = SSMParameterProvider(session=MagicMock(), client=MagicMock())
        cli._client.get_parameter_securestring_value.return_value = json.dumps({
            'a': 'not-rotated', 'the_secret_attribute': 'old-val'})
        cli._smclient = MagicMock()
        cli._smclient.generate_random_password.return_value = 'new-val'

        spec = {
            'key': 'secret_name',
            'provider': 'ssmparameterstore',
            'config': SSMParameterProvider.Options(
                rotate_attribute='the_secret_attribute')._asdict()
        }

        # Act
        return_val = cli.rotate(spec)

        # Assert
        self.assertEqual(return_val, {
            'a': 'not-rotated',
            'the_secret_attribute': 'new-val',
            'provider': 'ssmparameterstore'})

        cli._client.get_parameter_securestring_value.assert_called_once_with(spec['key'])
        cli._smclient.generate_random_password.assert_called_once_with(
            length=32,
            ExcludeCharacters='',
            ExcludeNumbers=False,
            ExcludePunctuation=False,
            ExcludeUppercase=False,
            ExcludeLowercase=False,
            IncludeSpace=False,
            RequireEachIncludedType=True,
        )

        cli._client.put_parameter_securestring.assert_called_once_with(
            param_name=spec['key'],
            param_value=json.dumps(return_val),
            description='',
        )

    def test_rotate_cant_get_current(self):
        cli = SSMParameterProvider(session=MagicMock(), client=MagicMock())
        cli._client.get_parameter_securestring_value.side_effect = GetParameterException

        spec = {
            'key': 'secret_name',
            'provider': 'secretsmanager',
            'config': SSMParameterProvider.Options(
                rotate_attribute='the_secret_attribute')._asdict()
        }

        with self.assertRaises(RotationException):
            cli.rotate(spec)

        cli._client.get_parameter_securestring_value.assert_called_once_with(spec['key'])

    def test_rotate_no_bypass_override_generated_pass_options(self):
        # Arrange
        cli = SSMParameterProvider(session=MagicMock(), client=MagicMock())
        cli._client.get_parameter_securestring_value.return_value = json.dumps({
            'a': 'not-rotated', 'the_secret_attribute': 'old-val'})

        cli._smclient = MagicMock()
        cli._smclient.generate_random_password.return_value = 'new-val'

        spec = {
            'key': 'secret_name',
            'provider': 'secretsmanager',
            'config': SSMParameterProvider.Options(
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
        cli._smclient.generate_random_password.assert_called_once_with(
            length=12,
            ExcludeCharacters='abc',
            ExcludeNumbers=True,
            ExcludePunctuation=True,
            ExcludeUppercase=True,
            ExcludeLowercase=True,
            IncludeSpace=True,
            RequireEachIncludedType=False,
        )

        cli._client.put_parameter_securestring.assert_called_once_with(
            param_name=spec['key'],
            param_value=json.dumps(return_val),
            description='',
        )

    def test_rotate_with_bypass(self):
        cli = SSMParameterProvider(session=MagicMock())
        cli._client = MagicMock()
        cli._client.get_parameter_securestring_value.return_value = json.dumps({
            'key1': 'val1'
        })

        result = cli.rotate({
            'key': 'secret_name',
            'provider': 'ssmparameterstore',
            'config': {
                'bypass': True
            }
        })

        self.assertEqual(result, {
            'key1': 'val1',
            'provider': 'ssmparameterstore'
        })
        cli._client.get_parameter_securestring_value.assert_called_once_with('secret_name')

    def test_validate_spec_base_fail(self):
        speci_valid = {
            'missing-provider': 'bananas',
            'key': 'abc'
        }

        r_result = SSMParameterProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)

    def test_validate_spec_no_config(self):
        speci_valid = {
            'provider': 'ssmparameterstore',
            'key': 'abc'
        }

        r_result = SSMParameterProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)

    def test_validate_spec_has_bypass_and_attr_name(self):
        speci_valid = {
            'provider': 'ssmparameterstore',
            'key': 'abc',
            'config': SSMParameterProvider.Options(
                bypass=True,
                rotate_attribute='my_pass'
            )._asdict()
        }

        r_result = SSMParameterProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)

    def test_validate_spec_with_source(self):
        speci_valid = {
            'provider': 'ssmparameterstore',
            'key': 'abc',
            'source': 'bananas'
        }

        r_result = SSMParameterProvider.validate_spec(speci_valid)
        self.assertEqual(r_result[0], True)

    def test_validate_spec_with_rotate_attribute(self):
        speci_valid = {
            'provider': 'ssmparameterstore',
            'key': 'abc',
            'config': {
                'rotate_attribute': 'my_pass',
                'length': 123
            }
        }

        r_result = SSMParameterProvider.validate_spec(speci_valid)
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

        r_result = SSMParameterProvider.redact_result(result)
        self.assertEqual(r_result, {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'cloudflare',
                'a': '***',
                'b': '***'
            }
        })
