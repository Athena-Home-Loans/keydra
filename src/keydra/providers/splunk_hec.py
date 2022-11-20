import boto3
import boto3.session
import json
import validators

import keydra.providers.splunk

from keydra import loader

from keydra.clients.splunk import SplunkClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger

LOGGER = get_logger()

USER_FIELD = 'hecInputName'
PW_FIELD = 'hecToken'
SPLUNK_USER_FIELD = keydra.providers.splunk.USER_FIELD
SPLUNK_PW_FIELD = keydra.providers.splunk.PW_FIELD


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None,
                 region_name=None, verify=False):

        if session is None:
            session = boto3.session.Session()

        self._session = session
        self._region = region_name

        self._credentials = credentials
        self._verify = verify

    def _rotate_secret(self, secret):
        '''
        Rotate token for a HEC input on a single Spunk server

        :param secret: The spec from the secrets yaml
        :type secret: :class:`dict`

        :returns: New secret ready to distribute
        :rtype: :class:`dict`
        '''

        host = secret['config']['host']

        # User the specified provider to load the operator secret
        secret_client = loader.load_client(
            secret['config']['rotatewith']['provider']
        )
        sclient = secret_client(
            session=self._session,
            region_name=self._region,
            credentials=self._credentials
        )

        operator_creds = json.loads(
            sclient.get_secret_value(
                secret_id=secret['config']['rotatewith']['key']
            )
        )
        username = operator_creds[SPLUNK_USER_FIELD]
        passwd = operator_creds[SPLUNK_PW_FIELD]

        try:
            LOGGER.debug('Connecting to Splunk')

            sp_client = SplunkClient(
                username=username,
                password=passwd,
                host=host,
                verify=self._verify
            )

            LOGGER.debug(
                'Successfully connected to Splunk host {}'.format(
                    host
                )
            )

            if host.endswith('splunkcloud.com'):
                LOGGER.debug('Rotating for Splunk Cloud.')

                newtoken = sp_client.rotate_hectoken_cloud(
                    inputname=self._credentials[USER_FIELD]
                )
            else:
                LOGGER.debug('Rotating for Splunk Enterprise.')

                newtoken = sp_client.rotate_hectoken(
                    inputname=self._credentials[USER_FIELD]
                )

        except Exception as e:
            LOGGER.error('Error: {}'.format(e))
            raise RotationException(
                'Error rotating HEC token for input {} on Splunk host '
                '{} - {}'.format(
                    self._credentials[USER_FIELD],
                    host,
                    e
                )
            ) from e

        return {
            f'{USER_FIELD}': self._credentials[USER_FIELD],
            f'{PW_FIELD}': newtoken
        }

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate_secret(secret)

    def distribute(self, secret, destination):
        raise DistributionException(
            'Splunk HEC provider does not support distribution'
        )

    @classmethod
    def validate_spec(cls, spec):
        if 'config' not in spec:
            return (False, "Required section 'config' not present in spec")

        if 'host' not in spec['config']:
            return (False, "Config must contain 'host'")

        host = spec['config']['host']
        if not validators.domain(host) and not validators.ipv4(host):
            return (False, 'Host {} must be a valid IP or domain name'.format(host))

        if 'rotatewith' not in spec['config']:
            return (False, "Config must contain 'rotatewith' section")
        else:
            if not all(k in spec['config']['rotatewith']
                       for k in ['key', 'provider']):
                return (False, "'rotatewith' must contain 'provider' and 'key'")

        return True, 'It is valid!'

    @classmethod
    def safe_to_log_keys(cls, spec) -> [str]:
        return BaseProvider.safe_to_log_keys(spec) + [USER_FIELD, SPLUNK_USER_FIELD]
