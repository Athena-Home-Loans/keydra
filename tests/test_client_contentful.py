import unittest

from unittest.mock import MagicMock
from unittest.mock import patch

from keydra.clients.contentful import ContentfulClient
from keydra.clients.contentful import ConnectionException

from contentful_management import Client
from contentful_management.array import Array
from contentful_management.personal_access_token import (
    PersonalAccessToken as PAT
)
from contentful_management.spaces_proxy import SpacesProxy

CREDS = {
    "provider": "contentful",
    "key": "test",
    "secret": "reyjgewjrygwj"
}


class TestContentfulClient(unittest.TestCase):
    @patch.object(SpacesProxy, 'all')
    @patch.object(Client, '__init__')
    def test__init(self, mk_client_init, mk_spaces):
        mk_client_init.return_value = None

        mk_spaces.return_value = Array(json={}, items={})

        cf_client = ContentfulClient(
                token=CREDS['key']
            )

        self.assertEqual(type(cf_client), ContentfulClient)

    @patch.object(SpacesProxy, 'all')
    @patch.object(Client, '__init__')
    def test__init_fail(self, mk_client_init, mk_spaces):
        mk_client_init.return_value = None
        mk_spaces.return_value = None

        with self.assertRaises(ConnectionException):
            ContentfulClient(
                token=CREDS['key']
            )

    @patch.object(ContentfulClient, '__init__')
    def test__revoke_token(self, mk_client_init):
        mk_client_init.return_value = None
        cf = ContentfulClient(
                token=CREDS['key']
            )
        cf._client = MagicMock()
        cf._client.personal_access_tokens().revoke = MagicMock()
        cf.revoke_token('id')

        cf._client.personal_access_tokens().revoke.assert_called_once_with(
            'id'
        )

    @patch.object(ContentfulClient, '__init__')
    def test__get_tokens(self, mk_client_init):
        mk_client_init.return_value = None
        cf = ContentfulClient(
                token=CREDS['key']
            )
        cf._client = MagicMock()
        cf._client.personal_access_tokens().all = MagicMock()
        cf._client.personal_access_tokens().all.return_value = [
            'token1', 'token2'
        ]

        g_result = cf.get_tokens()

        self.assertEqual(g_result, ['token1', 'token2'])
        cf._client.personal_access_tokens().all.assert_called_once_with()

    @patch.object(ContentfulClient, '__init__')
    def test__create_token_readonly(self, mk_client_init):
        mk_client_init.return_value = None
        cf = ContentfulClient(
                token=CREDS['key']
            )
        cf._client = MagicMock()
        cf._client.personal_access_tokens().create = MagicMock()
        cf._client.personal_access_tokens().create.return_value = PAT

        c_result = cf.create_token(name='TestToken')

        self.assertEqual(c_result, PAT)
        cf._client.personal_access_tokens().create.assert_called_once_with(
            {
                'name': 'TestToken',
                'scopes': ['content_management_read']
            }
        )

    @patch.object(ContentfulClient, '__init__')
    def test__create_token_readwrite(self, mk_client_init):
        mk_client_init.return_value = None
        cf = ContentfulClient(
                token=CREDS['key']
            )
        cf._client = MagicMock()
        cf._client.personal_access_tokens().create = MagicMock()
        cf._client.personal_access_tokens().create.return_value = PAT

        c_result = cf.create_token(name='TestToken', readonly=False)

        self.assertEqual(c_result, PAT)
        cf._client.personal_access_tokens().create.assert_called_once_with(
            {
                'name': 'TestToken',
                'scopes': ['content_management_manage']
            }
        )
