import boto3
import validators

from keydra.clients.salesforce import SalesforceClient

from keydra.clients.aws.secretsmanager import SecretsManagerClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger

LOGGER = get_logger()

PASS_LENGTH = 32


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None, region_name=None):
        self._sf_username = credentials['key']
        self._sf_token = credentials['token']
        self._sf_env = credentials['env']
        self._sf_domain = credentials['domain']

        if session is None:
            session = boto3.session.Session()

        self._smclient = SecretsManagerClient(
            session=session,
            region_name=region_name
        )

        self._client = SalesforceClient(
            username=self._sf_username,
            password=credentials['secret'],
            token=self._sf_token,
            domain=self._sf_domain
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

    def _rotate_secret(self, secret):
        # Generate new random password from SecretsManager
        new_passwd = self._generate_sforce_passwd(PASS_LENGTH)

        if len(new_passwd) != PASS_LENGTH:
            raise RotationException(
                'Failed to generate new password!'
            )

        # Change Salesforce password
        try:
            self._client.change_passwd(
                userid=self._client.get_user_id(self._sf_username),
                newpassword=new_passwd
            )

        except Exception as error:
            LOGGER.error(
                "Failed to change Salesforce password for user "
                "'{}'".format(self._sf_username)
            )

            raise RotationException(
                'Error rotating user {} on Salesforce - '
                'error : {}'.format(
                    self._sf_username,
                    error
                )
            )

        LOGGER.info(
            'Salesforce password changed successfully for user '
            "'{}'.".format(self._sf_username)
        )

        return {
            'provider': 'salesforce',
            'key': self._sf_username,
            'secret': new_passwd,
            'token': self._sf_token,
            'env': self._sf_env,
            'domain': self._sf_domain
        }

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate_secret(secret)

    def distribute(self, secret, destination):
        raise DistributionException('Salesforce does not support distribution')

    @classmethod
    def validate_spec(cls, spec):
        for k, v in spec.items():
            if not validators.length(k, min=2, max=75):
                return False, 'Key {} failed length checks'.format(k)
            if isinstance(v, list):
                for entry in v:
                    if isinstance(entry, dict):
                        if entry.get('provider', '').lower() != 'salesforce':
                            continue

                        if Client.validate_spec(entry)[0] is not True:
                            print(entry)
                            return False, 'Dict entry failed length checks'
                    else:
                        if validators.length(entry, min=2, max=75) is not True:
                            return False, 'List entry failed length checks'

            elif validators.length(v, min=2, max=75) is not True:
                return (False,
                        'Value for key {} failed length checks'.format(k))

        return True, 'It is valid!'

    @classmethod
    def redact_result(cls, result):
        if 'value' in result and 'secret' in result['value']:
            result['value']['secret'] = '***'
        if 'value' in result and 'token' in result['value']:
            result['value']['token'] = '***'

        return result
