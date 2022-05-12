from typing import NamedTuple
import boto3
import boto3.session

from keydra.clients.salesforce_marketing_cloud import SalesforceMarketingCloudClient

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
        subdomain_field: str = 'subdomain'
        business_unit_field: int = 'business_unit'
        mid_field: int = 'mid'

    def __init__(self, session=None, credentials: dict = None, region_name=None):
        if not credentials:
            raise ConfigException(
                'Credentials are required for Salesforce Marketing Cloud provider')

        self._orig_secret = credentials

        if session is None:
            session = boto3.session.Session()

        self._smclient = SecretsManagerClient(
            session=session,
            region_name=region_name
        )

    def _generate_sfmc_passwd(self, length):
        passwd = self._smclient.generate_random_password(
            length=length,
            IncludeSpace=False,
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

        client = SalesforceMarketingCloudClient(
            username=self._orig_secret[opts.user_field],
            password=self._orig_secret[opts.password_field],
            subdomain=self._orig_secret[opts.subdomain_field],
            mid=self._orig_secret[opts.mid_field],
            business_unit=self._orig_secret[opts.business_unit_field]
        )

        # Generate new random password from SecretsManager
        new_passwd = self._generate_sfmc_passwd(PASS_LENGTH)

        if len(new_passwd) != PASS_LENGTH:
            raise RotationException(
                'Failed to generate new password!'
            )

        # Change Salesforce Marketing Cloud password
        try:
            client.change_passwd(
                userid=self._orig_secret[opts.user_field],
                newpassword=new_passwd
            )

        except Exception as error:
            LOGGER.error(
                "Failed to change Salesforce Marketing Cloud password for user "
                "'{}'".format(self._orig_secret[opts.user_field])
            )

            raise RotationException(
                'Error rotating user {} on Salesforce Marketing Cloud - '
                'error : {}'.format(
                    self._orig_secret[opts.user_field],
                    error
                )
            )

        LOGGER.info(
            'Salesforce Marketing Cloud password changed successfully for user '
            "'{}'.".format(self._orig_secret[opts.user_field])
        )

        return {
            **self._orig_secret,
            f"{opts.password_field}": new_passwd
        }

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate_secret(secret)

    def distribute(self, secret, destination):
        raise DistributionException('Salesforce Marketing Cloud does not support distribution')

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
            for field in (
                opts.password_field, opts.business_unit_field, opts.mid_field, opts.subdomain_field
            ):
                if field in result['value']:
                    result['value'][field] = '***'

        return result
