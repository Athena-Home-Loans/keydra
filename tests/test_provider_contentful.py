import unittest

from keydra.providers import contentful

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from contentful_management.personal_access_token import (
    PersonalAccessToken as PAT
)

from unittest.mock import MagicMock
from unittest.mock import patch

CREDS = {
    "provider": "contentful",
    "key": "test",
    "secret": "reyjgewjrygwj"
}

SPEC = {
    'description': 'Test',
    'key': 'publicsite',
    'provider': 'contentful',
    'rotate': 'nightly',
    'distribute': [
        {
            'provider': 'secretsmanager',
            'source': 'secret',
            'key': 'keydra/contentful/publicsite',
            'envs': ['dev']
        }
    ]
}


class FakeToken(PAT):
    id = 1


class TestProviderContentful(unittest.TestCase):
    @patch.object(contentful.Client, '_rotate_secret')
    @patch.object(contentful, 'ContentfulClient')
    def test_rotate(self, mk_client, mk_rotate):
        cli = contentful.Client(credentials=CREDS, session=MagicMock(),
                                region_name='ap-southeast-2')

        cli.rotate('something')

        mk_rotate.assert_called_once_with('something')

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

        r_result = contentful.Client.redact_result(result)
        r_secret = r_result['value']['secret']

        self.assertNotEqual(r_secret, 'THIS_IS_SECRET')

    def test__redact_result_no_secrets(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret'
        }

        r_result = contentful.Client.redact_result(result)

        self.assertEqual(r_result, result)

    @patch.object(contentful, 'ContentfulClient')
    def test__create_token_fail(self, mk_client):
        cli = contentful.Client(credentials=CREDS, session=MagicMock(),
                                region_name='ap-southeast-2')

        cli._cfclient.create_token.side_effect = Exception('boom')

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPEC)

    @patch.object(contentful.ContentfulClient, 'create_token')
    @patch.object(contentful.ContentfulClient, 'get_tokens')
    @patch.object(contentful.ContentfulClient, 'revoke_token')
    @patch.object(contentful.ContentfulClient, '__init__')
    def test__revoke_tokens(self, mk_client, mk_revoke, mk_get, mk_create):
        mk_client.return_value = None
        cli = contentful.Client(credentials=CREDS, session=MagicMock(),
                                region_name='ap-southeast-2')

        mk_get.return_value = [
            FakeToken, FakeToken, FakeToken
        ]
        cli._rotate_secret(SPEC)

        self.assertEqual(mk_revoke.call_count, 3)

    @patch.object(contentful.ContentfulClient, 'create_token')
    @patch.object(contentful.ContentfulClient, 'get_tokens')
    @patch.object(contentful.ContentfulClient, 'revoke_token')
    @patch.object(contentful.ContentfulClient, '__init__')
    def test__revoke_token_except(self, mk_client, mk_rev, mk_get, mk_create):
        mk_client.return_value = None

        cli = contentful.Client(credentials=CREDS, session=MagicMock(),
                                region_name='ap-southeast-2')

        mk_get.return_value = [
            FakeToken, FakeToken, FakeToken
        ]
        mk_rev.side_effect = Exception('boom')

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPEC)

    @patch.object(contentful, 'ContentfulClient')
    def test__revoke_token_fail(self, mk_client):
        cli = contentful.Client(credentials=CREDS, session=MagicMock(),
                                region_name='ap-southeast-2')
        cli._cfclient = MagicMock()
        cli._cfclient.revoke_token = MagicMock()
        cli._cfclient.get_tokens = MagicMock()
        cli._cfclient.get_tokens.return_value = ['']

        with self.assertRaises(RotationException):
            cli._rotate_secret(SPEC)

    @patch.object(contentful, 'ContentfulClient')
    def test__distribute_exception(self, mk_client):
        cli = contentful.Client(credentials=CREDS, session=MagicMock(),
                                region_name='ap-southeast-2')

        with self.assertRaises(DistributionException):
            cli.distribute(secret='secret', destination='dest')
