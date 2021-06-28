import unittest

import keydra.clients.aws.kinesisfirehose as firehose

from keydra.clients.aws.kinesisfirehose import UpdateSecretException

from unittest.mock import MagicMock

SPLUNK_STREAM_DESC = {
    'DeliveryStreamDescription': {
        'VersionId': '11',
        'Destinations': [
            {
                'DestinationId': 'id1',
                'SplunkDestinationDescription': {}
            }
        ]
    }
}

HTTP_STREAM_DESC = {
    'DeliveryStreamDescription': {
        'VersionId': '22',
        'Destinations': [
            {
                'DestinationId': 'id11',
                'HttpEndpointDestinationDescription': {
                    'EndpointConfiguration': {'url': 'test'}
                }
            }
        ]
    }
}


class TestClientFirehose(unittest.TestCase):
    def test__stream_check(self):
        cli = firehose.FirehoseClient(session=MagicMock())
        cli._client.describe_delivery_stream = MagicMock()

        self.assertEqual(cli.stream_exists('woot'), True)

        cli._client.describe_delivery_stream.side_effect = Exception('boom!')
        self.assertEqual(cli.stream_exists('woot'), False)

    def test__get_stream_ids(self):
        cli = firehose.FirehoseClient(session=MagicMock())

        with self.assertRaises(Exception):
            cli._get_stream_ids('woot', 'limewire')

        cli._client.describe_delivery_stream.return_value = SPLUNK_STREAM_DESC

        self.assertEqual(cli._get_stream_ids('woot', 'Splunk'), ('11', 'id1'))
        self.assertEqual(cli._get_stream_ids('woot', 'HttpEndpoint'), ('11', None))

        cli._client.describe_delivery_stream.return_value = HTTP_STREAM_DESC
        self.assertEqual(cli._get_stream_ids('woot', 'HttpEndpoint'), ('22', 'id11'))

    def test__get_HttpEndpointConfiguration(self):
        cli = firehose.FirehoseClient(session=MagicMock())

        cli._client.describe_delivery_stream.return_value = HTTP_STREAM_DESC

        with self.assertRaises(Exception):
            cli._get_HttpEndpointConfiguration('woot', 'id88')

        self.assertEqual(cli._get_HttpEndpointConfiguration('woot', 'id11'), {'url': 'test'})

    def test__update_splunk_hectoken(self):
        cli = firehose.FirehoseClient(session=MagicMock())
        cli._client.describe_delivery_stream.return_value = HTTP_STREAM_DESC

        with self.assertRaises(UpdateSecretException):
            cli.update_splunk_hectoken('woot', 'key')

        cli._client.describe_delivery_stream.return_value = SPLUNK_STREAM_DESC
        cli._client.update_destination.return_value = {'hep'}
        self.assertEqual(cli.update_splunk_hectoken('woot', 'key'), {'hep'})

    def test__update_http_accesskey(self):
        cli = firehose.FirehoseClient(session=MagicMock())
        cli._client.describe_delivery_stream.return_value = SPLUNK_STREAM_DESC

        with self.assertRaises(UpdateSecretException):
            cli.update_http_accesskey('woot', 'key')

        cli._client.describe_delivery_stream.return_value = HTTP_STREAM_DESC
        cli._client.update_destination.return_value = {'hep'}
        self.assertEqual(cli.update_http_accesskey('woot', 'key'), {'hep'})
