from typing import NamedTuple
import boto3
import boto3.session

from keydra.clients.salesforce import SalesforceClient

from keydra.clients.aws.secretsmanager import SecretsManagerClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import ConfigException, DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger

LOGGER = get_logger()

PASS_LENGTH = 32


class Client(BaseProvider):
    class Options(NamedTuple):
        user_field: str = 'key'
        password_field: str = 'secret'
        token_field: str = 'token'
        domain_field: str = 'domain'

    def __init__(self, session=None, credentials: dict = None, region_name=None):
        if not credentials:
            raise ConfigException(
                'Credentials are required for Salesforce provider')

        self._orig_secret = credentials

        if session is None:
            session = boto3.session.Session()

        self._smclient = SecretsManagerClient(
            session=session,
            region_name=region_name
        )

    def _generate_sforce_passwd(self, length):
        # Excluding characters in order to mitigate known issue
        # https://trailblazer.salesforce.com/issues_view?id=a1p3A000000AT9rQAG
        passwd = self._smclient.generate_random_password(
            length=length,
            IncludeSpace=True,
            ExcludeCharacters='!"%&\'()*+,-./:;<=>?[\\]^_`{|}~$'
        )

        return passwd

    def _rotate_secret(self, spec):
        opts = Client.Options(**spec.get('config', {}))

        # Ensure the current secret is compatible with the spec for a successful rotation
        requiredFields = [getattr(opts, optField) for optField in opts._fields]
        missingFields = requiredFields - self._orig_secret.keys()
        if missingFields:
            raise RotationException(
                'The current value of {}::{} is missing required key(s): {}'.format(
                    spec['provider'],
                    spec['key'],
                    ' ,'.join(missingFields)))

        sf_user = self._orig_secret[opts.user_field]

        client = SalesforceClient(
            username=sf_user,
            password=self._orig_secret[opts.password_field],
            token=self._orig_secret[opts.token_field],
            domain=self._orig_secret[opts.domain_field]
        )

        # Generate new random password from SecretsManager
        new_passwd = self._generate_sforce_passwd(PASS_LENGTH)

        if len(new_passwd) != PASS_LENGTH:
            raise RotationException(
                'Failed to generate new password!'
            )

        # Change Salesforce password
        try:
            client.change_passwd(
                userid=client.get_user_id(sf_user),
                newpassword=new_passwd
            )

        except Exception as error:
            LOGGER.error(
                "Failed to change Salesforce password for user "
                "'{}'".format(sf_user)
            )

            raise RotationException(
                'Error rotating user {} on Salesforce - '
                'error : {}'.format(
                    sf_user,
                    error
                )
            )

        LOGGER.info(
            'Salesforce password changed successfully for user '
            "'{}'.".format(sf_user)
        )

        return {
            **self._orig_secret,
            f"{opts.password_field}": new_passwd
        }

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate_secret(secret)

    def distribute(self, secret, destination):
        raise DistributionException('Salesforce does not support distribution')

    @classmethod
    def validate_spec(cls, spec):
        valid, msg = BaseProvider.validate_spec(spec)

        if not valid:
            return False, msg

        unknown_fields = spec.get('config', {}).keys() - Client.Options._fields
        if unknown_fields:
            return False, 'Unknown config fields: ' + ', '.join(
                sorted(unknown_fields))

        return True, 'It is valid!'

    @classmethod
    def redact_result(cls, result, spec):
        opts = Client.Options(**spec.get('config', {}))

        if 'value' in result:
            for field in (opts.password_field, opts.token_field):
                if field in result['value']:
                    result['value'][field] = '***'

        return result
