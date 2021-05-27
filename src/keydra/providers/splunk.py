import boto3
import validators

from keydra.clients.splunk import SplunkClient

from keydra.clients.aws.secretsmanager import SecretsManagerClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger

LOGGER = get_logger()


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None,
                 region_name=None, verify=False):

        if session is None:
            session = boto3.session.Session()

        self._smclient = SecretsManagerClient(
            session=session,
            region_name=region_name
        )
        self._credentials = credentials
        self._verify = verify

    def _generate_splunk_passwd(self, length):
        '''
        Generate a random password from Secrets Manager

        :param length: Length of the new password
        :type username: :class:`int`

        :returns: New password as a string
        :rtype: :class:`passwd`
        '''
        passwd = self._smclient.generate_random_password(
            length=length,
            IncludeSpace=True
        )
        return passwd

    def _rotate_secret(self, secret):
        '''
        Rotate password for an account on a list of Spunk servers

        :param secret: The spec from the secrets yaml
        :type secret: :class:`dict`

        :returns: New secret ready to distribute
        :rtype: :class:`dict`
        '''
        username = self._credentials['key']
        current_passwd = self._credentials['secret']

        # Generate new random password from SecretsManager
        new_passwd = self._generate_splunk_passwd(32)

        # Change password on each Splunk host listed in the secret
        for host in secret['hosts']:
            try:
                sp_client = SplunkClient(
                    username=username,
                    password=current_passwd,
                    host=host,
                    verify=self._verify
                )
                sp_client.change_passwd(
                    username=username,
                    oldpasswd=current_passwd,
                    newpasswd=new_passwd
                )
            except Exception as e:
                raise RotationException(
                    'Error rotating user {} on Splunk host '
                    '{} - {}'.format(username, host, e)
                )

            LOGGER.info(
                'Successfully changed Splunk user {} ({}) on server {}'.format(
                    username,
                    secret['key'],
                    host
                )
            )

        return {
            'provider': 'splunk',
            'key': username,
            'secret': new_passwd
        }

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate_secret(secret)

    def _dist_storepass(self, client, destination, data):
        try:
            result = client.update_app_storepass(
                app=destination['config']['app'],
                username=data['name'],
                password=data['password'],
                realm=destination['config'].get('realm')
            )

        except Exception as e:
            raise DistributionException(
                'Error distributing secret to '
                'storage password {} of app {} on Splunk '
                'host {} - {}'.format(
                    data['name'],
                    destination['config']['app'],
                    destination['config']['host'],
                    e
                )
            )

        return result

    def _dist_custom(self, client, destination, data):
        try:
            result = client.update_app_config(
                app=destination['config']['app'],
                path=destination['config']['path'],
                obj=destination['key'],
                data=data
            )

        except Exception as e:
            raise DistributionException(
                'Error distributing secret to '
                'object {} of app {} on Splunk '
                'host {} - {}'.format(
                    destination['key'],
                    destination['config']['app'],
                    destination['config']['host'],
                    e
                )
            )

        return result

    def _distribute(self, secret, destination):
        '''
        Distribute credentials to Splunk as app config

        :param secret: The spec from the secrets yaml
        :type secret: :class:`dict`
        :param destination: The dest spec from the secrets yaml
        :type secret: :class:`dict`

        :returns: The spec as distributed
        :rtype: :class:`dict`
        '''

        # Connect to Splunk
        try:
            sp_client = SplunkClient(
                username=self._credentials['key'],
                password=self._credentials['secret'],
                host=destination['config']['host'],
                verify=self._verify
            )
        except Exception as error:
            LOGGER.error(
                'Could not connect to Splunk '
                'host {}: {}'.format(destination['config']['host'], error)
            )
            raise DistributionException(
                'Error distributing secret to '
                'app {} on Splunk '
                'host {} - {}'.format(
                    destination['key'],
                    destination['config']['app'],
                    destination['config']['host'],
                    error
                )
            )

        # Build post data. We want just the app specific stuff
        post_data = dict(**destination['config']['appconfig'])

        # Add the mapped values from the secret
        for mapdest, mapsrc in destination['source'].items():
            post_data[mapdest] = secret[mapsrc]

        # Are we just updating storage passwords like a good app?
        if destination['config'].get('path') is None:
            result = self._dist_storepass(
                client=sp_client,
                destination=destination,
                data=post_data
            )

        # No, we're doing something custom.
        else:
            result = self._dist_custom(
                client=sp_client,
                destination=destination,
                data=post_data
            )

        if result not in range(200, 299):
            raise DistributionException(
                'Error configuring app {} '
                'on Splunk host {}'.format(
                    destination['config']['app'],
                    destination['config']['host']
                )
            )

        LOGGER.info(
            'Splunk config distributed successfully '
            'to app {} on Splunk '
            'host {}'.format(
                destination['config']['app'],
                destination['config']['host']
            )
        )

        return destination

    @exponential_backoff_retry(3)
    def distribute(self, secret, destination):
        return self._distribute(secret, destination)

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

        if 'hosts' in spec:
            for host in spec['hosts']:
                if not validators.domain(host) and not validators.ipv4(host):
                    return (False, 'Host {} not valid'.format(host))

        return True, 'It is valid!'

    @classmethod
    def redact_result(cls, result, spec=None):
        if 'value' in result and 'secret' in result['value']:
            result['value']['secret'] = '***'

        return result
