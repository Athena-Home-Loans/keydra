import boto3
import boto3.session
import json
import validators

from keydra import loader

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

        self._session = session
        self._region = region_name

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

    def _rotate_user(self, secret, host, newpasswd):
        username = self._credentials['key']
        current_passwd = self._credentials['secret']

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
                newpasswd=newpasswd
            )
        except Exception as e:
            raise RotationException(
                'Error rotating user account {} on Splunk host '
                '{} - {}'.format(username, host, e)
            )

        return username, newpasswd

    def _rotate_hec_secret(self, secret, host):
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

        return secret['key'], newtoken

    def _rotate_secret(self, secret):
        '''
        Rotate password for an account on a list of Spunk servers

        :param secret: The spec from the secrets yaml
        :type secret: :class:`dict`

        :returns: New secret ready to distribute
        :rtype: :class:`dict`
        '''

        # Generate new random password from SecretsManager
        new_passwd = self._generate_splunk_passwd(32)

        # Change password on each Splunk host listed in the secret
        for host in secret['config']['hosts']:
            secrettype = secret['config'].get('type', 'user')

            if secrettype == 'user':
                key, password = self._rotate_user(
                    secret,
                    host=host,
                    newpasswd=new_passwd
                )

            if secrettype == 'hectoken':
                key, password = self._rotate_hec_secret(secret, host)

            LOGGER.info(
                'Successfully changed Splunk {} {} on server {}'.format(
                    secrettype,
                    key,
                    host
                )
            )

        return {
            'provider': 'splunk',
            'key': key,
            'secret': password
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
                'Error distributing secret {} to '
                'app {} on Splunk '
                'host {}: {}'.format(
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

        if 'config' not in spec:
            return (False, "Required section 'config' not present in spec")

        if 'hosts' not in spec['config']:
            return (False, "Config must contain hosts")

        for host in spec['config']['hosts']:
            if not validators.domain(host) and not validators.ipv4(host):
                return (False, 'Host {} not valid'.format(host))

        if 'type' in spec['config']:
            if spec['config']['type'] not in ['hectoken', 'user']:
                return (
                    False,
                    'Invalid Splunk secret type'.format(
                        spec['config']['type']
                    )
                )
            if spec['config']['type'] == 'hectoken':
                if 'rotatewith' not in spec['config']:
                    return (False, "Config must contain 'rotatewith' if HEC is the target")
                else:
                    if not all(k in spec['config']['rotatewith'] for k in ['key', 'provider']):
                        return (False, "'rotatewith' must contain 'provider' and 'key'")

                if len(spec['config']['hosts']) != 1:
                    return (False, "Only one host can be specified if HEC is the target")

        return True, 'It is valid!'

    @classmethod
    def redact_result(cls, result, spec=None):
        if 'value' in result and 'secret' in result['value']:
            result['value']['secret'] = '***'

        return result
