import boto3
import boto3.session

from keydra.clients.aws.kinesisfirehose import FirehoseClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger

LOGGER = get_logger()


class Client(BaseProvider):
    def __init__(self, session=None, region_name=None, credentials=None):
        if session is None:
            session = boto3.session.Session()

        self._client = FirehoseClient(
            session=session,
            region_name=region_name
        )

    def rotate(self, secret):
        raise RotationException('AWS Kinesis Firehose provider does not support rotation')

    def _distribute(self, secret, target):
        if not self._client.stream_exists(target['key']):
            raise DistributionException(
                "Stream '{}' not found! Does not exist or a you have a permissions issue".format(
                    target['key']
                )
            )

        try:
            if target['config']['dest_type'] == 'splunk':
                self._client.update_splunk_hectoken(
                    streamname=target['key'],
                    token=secret[target['source']]
                )
            elif target['config']['dest_type'] == 'http':
                self._client.update_http_accesskey(
                    streamname=target['key'],
                    key=secret[target['source']]
                )
            else:
                raise NotImplementedError(
                    'Firehose for destination type {} not implemented'.format(
                        target['config']['dest_type']
                    )
                )

        except Exception as e:
            raise DistributionException(e)

    @exponential_backoff_retry(3)
    def distribute(self, secret, target):
        return self._distribute(secret, target)

    @classmethod
    def validate_spec(cls, spec):
        valid, msg = BaseProvider.validate_spec(spec)

        if not valid:
            return valid, msg

        if 'config' not in spec:
            return False, 'Attribute "config" not present in configuration'

        if 'dest_type' not in spec['config']:
            return False, 'Attribute "dest_type" not present in configuration'

        if spec['config']['dest_type'] not in ['splunk', 'http']:
            return False, 'Unsupported dest type, must be splunk|http'

        return True, 'It is valid!'  # pragma: no cover
