import unittest

from botocore.exceptions import ClientError

from keydra.clients.aws.ssmparameterstore import SSMClient
from keydra.clients.aws.ssmparameterstore import GetParameterException, PutParameterException

from unittest.mock import MagicMock


CLIENT_ERR = ClientError(
    error_response={'Error': {'Code': 'boom'}},
    operation_name='opiv'
)


class TestSSMParamStoreClient(unittest.TestCase):
    def test__describe_parameters(self):
        cli = SSMClient(session=MagicMock())
        cli._client.describe_parameters = MagicMock()

        cli._client.describe_parameters.return_value = {
            'Parameters': [1]
        }
        self.assertEqual(cli.parameter_exists('woot'), True)

        cli._client.describe_parameters.return_value = {
            'Parameters': []
        }
        self.assertEqual(cli.parameter_exists('woot'), False)

    def test__get_param_success(self):
        cli = SSMClient(session=MagicMock())
        cli._client.get_parameter = MagicMock()

        cli._client.get_parameter.return_value = {
            'Parameter': {'Value': 'wootytooty'}
        }
        self.assertEqual(cli.get_parameter_securestring_value('woot'), 'wootytooty')

    def test__get_param_fail(self):
        cli = SSMClient(session=MagicMock())
        cli._client.get_parameter = MagicMock()
        cli._client.get_parameter.side_effect = CLIENT_ERR

        with self.assertRaises(GetParameterException):
            cli.get_parameter_securestring_value('woot')

    def test__put_param_success_param_exists(self):
        cli = SSMClient(session=MagicMock())
        cli._client = MagicMock()

        cli._client.put_parameter = MagicMock()

        cli.parameter_exists = MagicMock(return_value=True)

        api_resp = {
            'Version': 123,
            'Tier': 'Standard'
        }

        cli._client.put_parameter.return_value = api_resp

        self.assertEqual(
            cli.put_parameter_securestring(
                param_name='woot',
                param_value='toot',
                description='Some stuff'
            ),
            api_resp
        )
        cli._client.put_parameter.assert_called_once_with(
            Name='woot', Value='toot', Type='SecureString', Tier='Standard', Overwrite=True
        )

    def test__put_param_fail(self):
        cli = SSMClient(session=MagicMock())
        cli._client.put_parameter = MagicMock()
        cli._client.put_parameter.side_effect = CLIENT_ERR

        with self.assertRaises(PutParameterException):
            cli.put_parameter_securestring(
                param_name='woot',
                param_value='toot',
                description='Some stuff'
            )

    def test__put_param_success_param_not_exists(self):
        cli = SSMClient(session=MagicMock())
        cli._client = MagicMock()

        cli._client.put_parameter = MagicMock()

        cli.parameter_exists = MagicMock(return_value=False)

        api_resp = {
            'Version': 123,
            'Tier': 'Standard'
        }

        cli._client.put_parameter.return_value = api_resp

        self.assertEqual(
            cli.put_parameter_securestring(
                param_name='woot',
                param_value='toot',
                description='Some stuff'
            ),
            api_resp
        )
        cli._client.put_parameter.assert_called_once_with(
            Name='woot',
            Value='toot',
            Type='SecureString',
            Tier='Standard',
            Description='Some stuff',
            Tags=[{'Key': 'managedby', 'Value': 'keydra'}]
        )

    def test__put_param_specify_key(self):
        cli = SSMClient(session=MagicMock())
        cli._client = MagicMock()

        cli._client.put_parameter = MagicMock()

        cli.parameter_exists = MagicMock(return_value=False)
        cli.put_parameter_securestring(
            param_name='woot',
            param_value='toot',
            description='Some stuff',
            key_id='test'
        )

        cli._client.put_parameter.assert_called_once_with(
            Name='woot',
            Value='toot',
            Type='SecureString',
            Tier='Standard',
            KeyId='test',
            Description='Some stuff',
            Tags=[{'Key': 'managedby', 'Value': 'keydra'}]
        )
