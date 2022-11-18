import unittest

from unittest.mock import MagicMock
from unittest.mock import patch

from keydra.exceptions import DistributionException
from keydra.providers import aws_appsync

SECRET = {
  'description': 'Secret for appsync used by treasury integrations',
  'key': 'treasury-integrations',
  'config': {
      'api-id': 'lnd6axgaezalfb2ffhzrz4ryau'
  },
  'provider': 'appsync',
  'rotate': 'monthly'
}


class TestProviderAWSAppSync(unittest.TestCase):
    def test_redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'appsync',
                'key': 'KEY_ID',
                'secret': 'THIS_IS_SECRET'
            }
        }

        r_result = aws_appsync.Client.redact_result(result, {})

        self.assertEqual(r_result['value']['provider'], 'appsync')
        self.assertEqual(r_result['value']['key'], 'KEY_ID')
        self.assertEqual(r_result['value']['secret'], '***')

    def test_validate_spec_valid(self):
        speci_valid = {
            'secret': 'shhhhhhh tell no one',
            'key': 'treasury',
            'config': {
                'api-id': 'test'
            },
            'provider': 'appsync',
            'rotate': 'nightly'
        }

        r_result = aws_appsync.Client.validate_spec(speci_valid)
        self.assertEqual(r_result[0], True)

    def test_validate_spec_invalid(self):
        spec_invalid = {
            'blablabla': 'blaaaa',
            'key': 'api-id',
            'provider': 'appsync',
            'rotate': 'nightly'
        }

        r_result = aws_appsync.Client.validate_spec(spec_invalid)
        self.assertEqual(r_result[0], False)

    @patch.object(aws_appsync, 'AppSyncClient')
    def test__distribute_exception(self, mk_sf_client):
        cli = aws_appsync.Client(
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        with self.assertRaises(DistributionException):
            cli.distribute(secret='secret', destination='dest')

    @patch.object(aws_appsync, 'AppSyncClient')
    def test__generate_new_api_key(self, mk_sforce):
        cli = aws_appsync.Client(
            session=MagicMock(),
            region_name='ap-southeast-2'
        )

        new_api_key = 'new_api_key'
        cli._appsync_client = MagicMock()
        cli._appsync_client.create_api_key.return_value = {
                    'apiKey': {
                        'id': new_api_key,
                        'description': 'string',
                        'expires': 123
                    }
                }

        cli._appsync_client.delete_api_key.return_value = {}
        cli._appsync_client.list_api_keys.return_value = {
                    'apiKeys': []
        }
        test_url = 'https://corp.com.au/api/graphql'
        cli._appsync_client.get_graphql_api.return_value = {
            'graphqlApi': {
                'uris': {
                    'GRAPHQL': test_url
                }
            }
        }

        r_result = cli.rotate(SECRET)

        self.assertEqual(r_result['secret'], new_api_key)
        self.assertEqual(r_result['url'], test_url)
