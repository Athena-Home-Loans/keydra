import boto3
import boto3.session
import json
import validators

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
        username = operator_creds['key']
        passwd = operator_creds['secret']

        try:
            sp_client = SplunkClient(
                username=username,
                password=passwd,
                host=host,
                verify=self._verify
            )
            newtoken = sp_client.rotate_hectoken(
                inputname=secret['key']
            )

        except Exception as e:
            raise RotationException(
                'Error rotating HEC token for input {} on Splunk host '
                '{} - {}'.format(secret['key'], host, e)
            )

        return {
            f'{USER_FIELD}': secret['key'],
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
    def redact_result(cls, result, spec=None):
        if 'value' in result and PW_FIELD in result['value']:
            result['value'][PW_FIELD] = '***'

        return result
