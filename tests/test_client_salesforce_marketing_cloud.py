import unittest

from unittest.mock import MagicMock
from unittest.mock import patch

from keydra.clients.salesforce_marketing_cloud import SalesforceMarketingCloudClient

TEST_DATA = {
    "username": "test",
    "password": "pass",
    "newpass": "pass2",
    "subdomain": "abc@_!xyz",
    "mid": 123456789,
    "businessunit": 987654321,
    'statusOk': 'OK',
    'statusMaint': 'InMaintenance',
    'statusOut': 'UnplannedOutage'
}


class TestSalesforceMarketingClient(unittest.TestCase):

    @classmethod
    @patch('keydra.clients.salesforce_marketing_cloud.Client')
    def setUpClass(self, mk_zeep_client):
        # Init Salesforce Marketing Client once for all tests
        mk_zeep_client.return_value = None
        self.sfmc_client = SalesforceMarketingCloudClient(
            username=TEST_DATA['username'],
            password=TEST_DATA['password'],
            subdomain=TEST_DATA['subdomain'],
            mid=TEST_DATA['mid'],
            businessUnit=TEST_DATA['businessunit'],
        )
        self.sfmc_client._client = MagicMock()

    def test__init(self):
        self.assertIsNotNone(self.sfmc_client)
        self.assertEqual(self.sfmc_client._businessUnit, TEST_DATA['businessunit'])
        self.assertEqual(self.sfmc_client._mid, TEST_DATA['mid'])
        self.assertEqual(self.sfmc_client._headers, {
            'SOAPAction': 'Update', 'Content-Type': 'text/xml'
        })

    def test__sfmc_get_status(self):
        self.sfmc_client._client = MagicMock()
        self.sfmc_client._client.service.GetSystemStatus.return_value = {'OverallStatus': 'OK'}
        self.assertEqual(self.sfmc_client.get_sfmc_status(), TEST_DATA['statusOk'])

        self.sfmc_client._client.service.GetSystemStatus.return_value = {
            'OverallStatus': 'InMaintenance'
        }
        self.assertEqual(self.sfmc_client.get_sfmc_status(), TEST_DATA['statusMaint'])

        self.sfmc_client._client.service.GetSystemStatus.return_value = {
            'OverallStatus': 'UnplannedOutage'
        }
        self.assertEqual(self.sfmc_client.get_sfmc_status(), TEST_DATA['statusOut'])

    @patch.object(SalesforceMarketingCloudClient, 'get_sfmc_status')
    def test__changepw_success(self, mk_status):
        mk_status.return_value = TEST_DATA['statusOk']
        self.sfmc_client._client.service.Update.return_value = {
            'Results': [{'StatusCode': 'OK', 'StatusMessage': 'Account User Updated / Created'}]
        }

        result = self.sfmc_client.change_passwd(
                TEST_DATA['username'],
                TEST_DATA['newpass']
            )
        self.assertTrue(result)

    @patch.object(SalesforceMarketingCloudClient, 'get_sfmc_status')
    def test__changepw_fail(self, mk_status):
        mk_status.return_value = TEST_DATA['statusOk']
        self.sfmc_client._client.service.Update.return_value = {
            'Results': [{'StatusCode': 'Error'}]
        }

        with self.assertRaises(Exception):
            self.sfmc_client.change_passwd(
                TEST_DATA['username'],
                TEST_DATA['newpass']
            )

    @patch.object(SalesforceMarketingCloudClient, 'get_sfmc_status')
    def test_changepw_system_error(self, mk_status):
        mk_status.return_value = TEST_DATA['statusOut']

        with self.assertRaises(Exception):
            self.sfmc_client.change_passwd(
                TEST_DATA['username'],
                TEST_DATA['newpass']
            )
