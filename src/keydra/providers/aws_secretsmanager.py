import boto3
import boto3.session
import json

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException

from typing import Dict, NamedTuple, Optional
from keydra.exceptions import RotationException

from keydra.clients.aws.secretsmanager import GetSecretException
from keydra.clients.aws.secretsmanager import InsertSecretException
from keydra.clients.aws.secretsmanager import SecretsManagerClient
from keydra.clients.aws.secretsmanager import UpdateSecretException

from keydra.logging import get_logger


LOGGER = get_logger()


class SecretsManagerProvider(BaseProvider):
    def __init__(
            self,
            session=None,
            client: SecretsManagerClient = None,
            region_name=None,
            # credentials must be present for the loader to init the provider
            credentials=None):
        if session is None:  # pragma: no cover
            session = boto3.session.Session()

        self._client = client or SecretsManagerClient(
            session=session,
            region_name=region_name
        )

    class Options(NamedTuple):
        bypass: bool = False
        rotate_attribute: Optional[str] = None
        length: int = 32
        exclude_char: str = ''
        exclude_num: bool = False
        exclude_punct: bool = False
        exclude_upper: bool = False
        exclude_lower: bool = False
        include_space: bool = False
        require_each_type: bool = True

    def _distribute_secret(self, secret, dest):
        current_secret = None

        try:
            current_secret = self._client.describe_secret(
                secret_id=dest['key']
            )
        except GetSecretException as e:
            print('not existing, ', e)
            LOGGER.info(
                '{} not present in SecretsManager: {}'.format(dest['key'], e)
            )

        try:
            if current_secret:
                print('present, updating ', dest)
                LOGGER.info(
                    '{} is present in SecretsManager, updating.'.format(
                        dest['key']
                    )
                )

                self._client.update_secret(
                    secret_id=dest['key'],
                    secret_value=json.dumps(secret)
                )

            else:
                print('not present, creating')
                LOGGER.info(
                    '{} not present in SecretsManager, adding.'.format(
                        dest['key'],
                    )
                )

                self._client.create_secret(
                    secret_name=dest['key'],
                    secret_value=json.dumps(secret),
                    description='Keydra managed secret {}'.format(
                        dest['key']
                    )
                )

        except (InsertSecretException, UpdateSecretException) as e:
            raise DistributionException(
                'Error distributing {}: {}'.format(dest['key'], e)
            )

        LOGGER.info(
            'Successfully distributed {} to SecretsManager from {}'.format(
                dest['key'],
                secret['provider']
            )
        )

        return dest

    def _get_current_secret(self, secret_key):
        try:
            value = self._client.get_secret_value(secret_key)

            # Assume that all secret values are formatted as valid JSON objects
            obj = json.loads(value)
            obj['provider'] = 'secretsmanager'

            return obj

        except Exception as e:
            raise RotationException(e)

    def _generate_secret_value(self, opts: Options) -> str:
        return self._client.generate_random_password(
            length=opts.length,
            ExcludeCharacters=opts.exclude_char,
            ExcludeNumbers=opts.exclude_num,
            ExcludePunctuation=opts.exclude_punct,
            ExcludeUppercase=opts.exclude_upper,
            ExcludeLowercase=opts.exclude_lower,
            IncludeSpace=opts.include_space,
            RequireEachIncludedType=opts.require_each_type)

    def rotate(self, spec) -> Dict[str, str]:
        current_secret = self._get_current_secret(spec['key'])

        options = SecretsManagerProvider.Options(**spec['config'])

        if options.bypass:
            LOGGER.debug('Bypassing rotation for {}'
                         .format(spec['key']))
            return current_secret

        LOGGER.debug('Rotating {} with options: {}'
                     .format(spec['key'], options))

        current_secret[options.rotate_attribute] = \
            self._generate_secret_value(options)

        self._client.update_secret(
            spec['key'],
            json.dumps(current_secret))

        return current_secret

    @exponential_backoff_retry(3)
    def distribute(self, secret, destination):
        try:
            return self._distribute_secret(secret, destination)
        except Exception as e:
            raise DistributionException(e)

    @classmethod
    def validate_spec(cls, spec):
        valid, msg = BaseProvider.validate_spec(spec)

        if not valid:
            return False, msg

        if ('config' in spec) == ('source' in spec):
            return False, 'Must specify either "config" or \
                "source", not both'

        if 'source' in spec:
            return True, 'All good!'

        options = SecretsManagerProvider.Options(**spec['config'])

        if options.bypass == (options.rotate_attribute is not None):
            return False, 'Must specify either "bypass" or \
                "rotate_attribute", not both'

        return True, 'All good!'

    @classmethod
    def redact_result(cls, result, spec=None):
        if 'value' in result:
            for key, value in result['value'].items():
                if key != 'provider':
                    result['value'][key] = '***'

        return result
