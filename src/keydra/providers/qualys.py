import boto3
import json
import validators

from keydra.clients.qualys import QualysClient
from keydra.clients.aws.secretsmanager import SecretsManagerClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger

LOGGER = get_logger()


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None, region_name=None):

        if session is None:
            session = boto3.session.Session()

        smclient = SecretsManagerClient(
            session=session,
            region_name=region_name
        )

        operator_creds = json.loads(
            smclient.get_secret_value(credentials['rotatewith'])
        )

        self._operator = operator_creds['username']
        self._credentials = credentials

        self._client = QualysClient(
            platform=operator_creds['platform'],
            username=operator_creds['username'],
            password=operator_creds['password']
        )

    def _rotate_secret(self, secret):
        '''
        Rotate password for an account

        :param secret: The spec from the secrets yaml
        :type secret: :class:`dict`

        :returns: New secret ready to distribute
        :rtype: :class:`dict`
        '''
        resp = self._credentials
        resp['provider'] = 'qualys'

        try:
            resp['password'] = self._client.change_passwd(
                username=self._credentials['username']
            )

        except Exception as e:
            print(e)
            raise RotationException(
                'Error rotating user {} (with user {}). Reason: {}'.format(
                    self._credentials['username'],
                    self._operator,
                    e
                )
            )

        LOGGER.info(
            'Successfully changed Qualys user {}'.format(
                self._credentials['username']
            )
        )

        return resp

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate_secret(secret)

    def distribute(self, secret, destination):
        raise DistributionException('Qualys does not support distribution')

    @classmethod
    def validate_spec(cls, spec):

        for k, v in spec.items():
            if not validators.length(k, min=2, max=75):
                return False, 'Key {} failed length checks'.format(k)

            # Don't key check lists, as it will check length of list not str
            if (not isinstance(v, list) and
                    not validators.length(v, min=2, max=75)):
                return (False,
                        'Value for key {} failed length checks'.format(k))

        return True, 'It is valid!'

    @classmethod
    def redact_result(cls, result):
        if 'value' in result and 'password' in result['value']:
            result['value']['password'] = '***'

        return result
