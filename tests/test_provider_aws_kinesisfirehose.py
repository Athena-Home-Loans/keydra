import uuid
import unittest

from keydra.exceptions import DistributionException, RotationException

from keydra.providers import aws_kinesisfirehose

from unittest.mock import MagicMock
from unittest.mock import patch

SPLUNK_SECRET = {
    'hhecInputName': 'Test',
    'hecToken': uuid.uuid4()
}

DEST_SPLUNK = {
    'provider': 'firehose',
    'source': 'hecToken',
    'key': 'Test',
    'config': {
        'dest_type': 'splunk'
    },
    'envs': [
        'dev'
    ]
}

DEST_HTTP = {
    'provider': 'firehose',
    'source': 'hecToken',
    'key': 'Test',
    'config': {
        'dest_type': 'http'
    },
    'envs': [
        'dev'
    ]
}

DEST_BAD = {
    'provider': 'firehose',
    'source': 'hecToken',
    'key': 'Test',
    'config': {
        'dest_type': 'woot'
    },
    'envs': [
        'dev'
    ]
}

DEST_NO_DEST = {
    'provider': 'firehose',
    'source': 'hecToken',
    'key': 'Test',
    'config': {
    },
    'envs': [
        'dev'
    ]
}

DEST_NO_CFG = {
    'provider': 'firehose',
    'source': 'hecToken',
    'key': 'Test',
    'envs': [
        'dev'
    ]
}


class TestProviderFirehose(unittest.TestCase):
    @patch.object(aws_kinesisfirehose, 'FirehoseClient')
    def test__dist_splunk(self,  mk_hose):
        cli = aws_kinesisfirehose.Client(
            session=MagicMock()
        )
        cli._distribute(SPLUNK_SECRET, DEST_SPLUNK)

        self.assertEqual(mk_hose().update_splunk_hectoken.call_count, 1)

    @patch.object(aws_kinesisfirehose, 'FirehoseClient')
    def test__dist_http(self,  mk_hose):
        cli = aws_kinesisfirehose.Client(
            session=MagicMock()
        )
        cli._distribute(SPLUNK_SECRET, DEST_HTTP)

        self.assertEqual(mk_hose().update_http_accesskey.call_count, 1)

    @patch.object(aws_kinesisfirehose, 'FirehoseClient')
    def test__dist_unknown_dest(self,  mk_hose):
        cli = aws_kinesisfirehose.Client(
            session=MagicMock()
        )

        with self.assertRaises(DistributionException):
            cli._distribute(SPLUNK_SECRET, DEST_BAD)

    def test__rotate(self):
        cli = aws_kinesisfirehose.Client(
            session=MagicMock()
        )
        with self.assertRaises(RotationException):
            cli.rotate(SPLUNK_SECRET)

    @patch.object(aws_kinesisfirehose, 'FirehoseClient')
    def test__dist_unknown_stream(self,  mk_hose):
        cli = aws_kinesisfirehose.Client(
            session=MagicMock()
        )
        mk_hose().stream_exists.return_value = False

        with self.assertRaises(DistributionException):
            cli._distribute(SPLUNK_SECRET, DEST_BAD)

    def test__validate_splunk_good(self):
        cli = aws_kinesisfirehose.Client(
            session=MagicMock()
        )

        res = cli.validate_spec(DEST_SPLUNK)

        self.assertEqual(res, (True, 'It is valid!'))

    def test__validate_bad_cases(self):
        cli = aws_kinesisfirehose.Client(
            session=MagicMock()
        )

        self.assertEqual(
            cli.validate_spec(DEST_BAD),
            (False, 'Unsupported dest type, must be splunk|http')
        )

        self.assertEqual(
            cli.validate_spec(DEST_NO_DEST),
            (False, 'Attribute "dest_type" not present in configuration')
        )

        self.assertEqual(
            cli.validate_spec(DEST_NO_CFG),
            (False, 'Attribute "config" not present in configuration')
        )
