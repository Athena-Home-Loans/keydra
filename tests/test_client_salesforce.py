import unittest

from unittest.mock import MagicMock
from unittest.mock import patch

from keydra.clients.salesforce import SalesforceClient
from keydra.clients.salesforce import ValidationException


SF_CREDS = {
    "provider": "salesforce",
    "key": "test@test.com",
    "secret": "test",
    "token": "token",
    "env": "dev11",
    "domain": "test"
}


class TestSalesforceClient(unittest.TestCase):
    @patch.object(SalesforceClient, '__init__')
    def test__userid_except(self, mk_client_init):
        mk_client_init.return_value = None
        sf_client = SalesforceClient(
                username=SF_CREDS['key'],
                password=SF_CREDS['secret'],
                token=SF_CREDS['token'],
                domain=SF_CREDS['domain']
            )
        sf_client._client = MagicMock()

        with self.assertRaises(Exception):
            sf_client.get_user_id('test@test.com')

    @patch.object(SalesforceClient, '__init__')
    def test__userid_email_invalid(self, mk_client_init):
        mk_client_init.return_value = None
        sf_client = SalesforceClient(
                username=SF_CREDS['key'],
                password=SF_CREDS['secret'],
                token=SF_CREDS['token'],
                domain=SF_CREDS['domain']
            )
        sf_client._client = MagicMock()

        with self.assertRaises(ValidationException):
            sf_client.get_user_id('test')

    @patch.object(SalesforceClient, '__init__')
    def test__userid_two_results(self, mk_client_init):
        mk_client_init.return_value = None
        sf_client = SalesforceClient(
                username=SF_CREDS['key'],
                password=SF_CREDS['secret'],
                token=SF_CREDS['token'],
                domain=SF_CREDS['domain']
            )
        sf_client._client = MagicMock()
        sf_client._client.query.return_value = {'totalSize': 2}

        with self.assertRaises(Exception):
            sf_client.get_user_id('test@test.com')

    @patch.object(SalesforceClient, '__init__')
    def test__userid_success(self, mk_client_init):
        mk_client_init.return_value = None
        sf_client = SalesforceClient(
                username=SF_CREDS['key'],
                password=SF_CREDS['secret'],
                token=SF_CREDS['token'],
                domain=SF_CREDS['domain']
            )
        sf_client._client = MagicMock()
        sf_client._client.query.return_value = {
            'totalSize': 1, 'records': [{'Id': '1234'}]
        }

        g_result = sf_client.get_user_id('test@test.com')
        self.assertEqual(g_result, '1234')

    @patch.object(SalesforceClient, '__init__')
    def test__changepw_success(self, mk_client_init):
        mk_client_init.return_value = None
        sf_client = SalesforceClient(
                username=SF_CREDS['key'],
                password=SF_CREDS['secret'],
                token=SF_CREDS['token'],
                domain=SF_CREDS['domain']
            )
        sf_client._client = MagicMock()
        sf_client._base_url = MagicMock()
        sf_client._client._call_salesforce.return_value.status_code = 200

        g_result = sf_client.change_passwd('1234', 'Password123')
        self.assertEqual(g_result, True)

    @patch.object(SalesforceClient, '__init__')
    def test__changepw_fail(self, mk_client_init):
        mk_client_init.return_value = None
        sf_client = SalesforceClient(
                username=SF_CREDS['key'],
                password=SF_CREDS['secret'],
                token=SF_CREDS['token'],
                domain=SF_CREDS['domain']
            )
        sf_client._client = MagicMock()
        sf_client._base_url = MagicMock()
        sf_client._client._call_salesforce.return_value.status_code = 400

        with self.assertRaises(Exception):
            sf_client.change_passwd('1234', 'Password123')

    @patch('keydra.clients.salesforce.Salesforce')
    def test__connect_prod(self, mk_sf):
        SalesforceClient(
                username=SF_CREDS['key'],
                password=SF_CREDS['secret'],
                token=SF_CREDS['token'],
                domain='prod'
            )

        mk_sf.assert_called_once_with(
            domain=None,
            password='test',
            security_token='token',
            username='test@test.com'
        )

    @patch('keydra.clients.salesforce.Salesforce')
    def test__connect_dev(self, mk_sf):
        SalesforceClient(
                username=SF_CREDS['key'],
                password=SF_CREDS['secret'],
                token=SF_CREDS['token'],
                domain='test'
            )

        mk_sf.assert_called_once_with(
            domain='test',
            password='test',
            security_token='token',
            username='test@test.com'
        )
