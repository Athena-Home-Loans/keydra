import boto3
import boto3.session
import json

from keydra.clients.qualys import QualysClient

from keydra import loader

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger

LOGGER = get_logger()

USER_FIELD = 'username'
PW_FIELD = 'password'


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None, region_name=None):

        if session is None:
            session = boto3.session.Session()

        self._session = session
        self._region = region_name
        self._credentials = credentials

    def _rotate_secret(self, secret):
        '''
        Rotate password for an account

        :param secret: The spec from the secrets yaml
        :type secret: :class:`dict`

        :returns: New secret ready to distribute
        :rtype: :class:`dict`
        '''
        if self._credentials is None:
            raise RotationException(
                'No credentials provided to provider on init, '
                'this is required.'
            )

        resp = self._credentials
        resp['provider'] = 'qualys'

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

        qclient = QualysClient(
            platform=operator_creds['platform'],
            username=operator_creds[USER_FIELD],
            password=operator_creds[PW_FIELD]
        )

        try:
            resp[PW_FIELD] = qclient.change_passwd(
                username=self._credentials[USER_FIELD]
            )

        except Exception as e:
            raise RotationException(
                'Error rotating user {} (with user {}). Reason: {}'.format(
                    self._credentials[USER_FIELD],
                    operator_creds[USER_FIELD],
                    e
                )
            )

        LOGGER.info(
            'Successfully changed Qualys user {}'.format(
                self._credentials[USER_FIELD]
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
        valid, msg = BaseProvider.validate_spec(spec)

        if not valid:
            return valid, msg

        if 'config' not in spec:
            return False, 'Attribute "config" not present in configuration'

        if 'rotatewith' not in spec['config']:
            return False, 'Attribute "rotatewith" not present in configuration'

        req_keys = ['key', 'provider']
        if not all(key in spec['config']['rotatewith'] for key in req_keys):
            return False, '"config" stanza must include keys {}'.format(
                ", ".join(req_keys)
            )

        return True, 'It is valid!'     # pragma: no cover

    @classmethod
    def safe_to_log_keys(cls, spec) -> [str]:
        return BaseProvider.safe_to_log_keys(spec) + [USER_FIELD]
