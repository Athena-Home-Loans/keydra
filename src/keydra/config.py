import copy
import math

from keydra import loader

from keydra.exceptions import ConfigException
from keydra.exceptions import InvalidSecretProvider

from keydra.logging import get_logger

KEYDRA_CONFIG_REPO = 'keydra-config'

REMOTE_CONFIG_ENVS = 'src/main/dist/environments.yaml'
REMOTE_CONFIG_SECRETS = 'src/main/dist/secrets.yaml'

ENVS_SPEC = ['type', 'secrets']
ENV_TYPE_SPEC = {
    'aws': ['description', 'access', 'id']
}
SECRETS_SPEC = ['key', 'provider']
SECRET_ENV_SPEC = ['key', 'provider', 'source', 'envs']

ALLOWED_ROTATION_SCHEDULES = ['nightly',
                              'weekly',
                              'monthly',
                              'adhoc',
                              'canaries']

LOGGER = get_logger()


class KeydraConfig(object):
    def __init__(self, config, session=None, **kwargs):
        if 'provider' not in config:
            raise ConfigException('"provider" not present in config')

        if 'config' not in config:
            raise ConfigException('"config" not present in config')

        self._sts = session.client('sts')
        self._config = config

    def _fetch_current_account(self):
        return self._sts.get_caller_identity()['Account']

    def _validate_spec(self, environments, secrets):
        for env, env_desc in environments.items():
            for key in ENVS_SPEC:
                if key not in env_desc:
                    raise ConfigException(
                        'Environment is missing attribute: {}'.format(key)
                    )

            for key in ENV_TYPE_SPEC.get(env_desc['type'], {}):
                if key not in env_desc:
                    raise ConfigException(
                        'AWS Environment is missing attribute: {}'.format(key)
                    )

            for secret in env_desc.get('secrets', []):
                if secret not in secrets:
                    raise ConfigException(
                        'Secret "{}" specified in "{}" is defined in '
                        'secrets.yaml'.format(secret, env)
                    )

        for sid, secret in secrets.items():
            for key in SECRETS_SPEC:
                if key not in secret:
                    raise ConfigException(
                        'Secret {} is missing attribute: {}'.format(sid, key)
                    )

            if 'rotate' in secret:
                if secret['rotate'] not in ALLOWED_ROTATION_SCHEDULES:
                    raise ConfigException(
                        'Secret "{}" has an invalid rotation schedule: {} '
                        '(allowed: {})'.format(
                            sid, secret['rotate'], ', '.join(
                                ALLOWED_ROTATION_SCHEDULES
                            )
                        )
                    )

            for env in secret.get('distribute', []):
                for key in SECRET_ENV_SPEC:
                    if key not in env:
                        raise ConfigException(
                            'Secret distribute is missing attribute: {}'
                            .format(key)
                        )

                for env_restr in env['envs']:
                    if env_restr == '*':
                        continue

                    if env_restr not in set(environments.keys()):
                        raise ConfigException(
                            'Environment "{}" from secrets.yaml is not '
                            'present in environments.yaml'.format(env_restr)
                        )

    def _guess_current_environment(self, environments):
        account_id = self._fetch_current_account()
        LOGGER.debug('Attempting to identify the environment from account {}'
                     .format(account_id))

        for env, desc in environments.items():
            if desc['type'] != 'aws':
                continue

            if str(desc['id']) == str(account_id):
                return env

        raise ConfigException('No environment is mapped to AWS account {}'
                              .format(account_id))

    def _filter(self, environments, specs, rotate='adhoc',
                requested_secrets=None, number_of_batches: int = None, batch_number: int = None):
        filtered_secrets = []
        current_env_name = self._guess_current_environment(environments)
        current_env = environments[current_env_name]

        if rotate == 'adhoc' and not requested_secrets:
            LOGGER.warn('AdHoc runs need to specify the secrets to rotate')

            return filtered_secrets

        candidate_secrets = specs

        if number_of_batches is not None and batch_number is not None:
            if not isinstance(number_of_batches, int) or not isinstance(batch_number, int):
                raise Exception(
                    f"batch number {batch_number} or number of batches {number_of_batches} is not an integer")

            if batch_number >= number_of_batches or number_of_batches <= 0 or batch_number < 0:
                raise Exception(f"batch number {batch_number} and number of batches {batch_number} is not valid")
            batch_size = math.ceil(len(candidate_secrets) / number_of_batches)
            starting_index = batch_size * batch_number  # assumption that batch number starts from zero
            if rotate == 'nightly':
                # Only rotate the first batch of secrets
                LOGGER.info(
                    'Batching batch number %s, batch size of %s, number of batches %s, secrets for nightly rotation',
                    batch_number, batch_size, number_of_batches)
                candidate_secrets = dict((k, v) for k, v in list(
                    candidate_secrets.items())[starting_index: starting_index + batch_size])

        for sid, secret in candidate_secrets.items():
            if requested_secrets and sid not in requested_secrets:
                LOGGER.debug(
                    'Skipping {} as it was not included in the request ({})'
                    .format(sid, requested_secrets))
                continue

            if sid not in current_env['secrets']:
                LOGGER.debug(
                    'Skipping {} as it is not listed for environment: {}'
                    .format(sid, current_env_name))
                continue

            if secret.get('rotate', 'adhoc') != rotate and rotate != 'adhoc':
                LOGGER.debug(
                    'Skipping {} as its rotation period ({}) doesn\'t '
                    'match current ({})'
                    .format(secret, secret.get('rotate', 'adhoc'), rotate))
                continue

            if 'distribute' not in secret:
                filtered_secrets.append(secret)
                continue

            current_secret = copy.deepcopy(secret)
            current_secret['distribute'] = []
            context = {
                'environment': {current_env_name: current_env},
                'action': 'distribute',
                'rotate': rotate
            }

            for target in secret['distribute']:
                for env in target['envs']:
                    if env != '*' and env != current_env_name:
                        continue

                    try:
                        provider = loader.load_provider_client(
                            target['provider']
                        )

                        new_spec = provider.pre_process_spec(
                            target, context=context
                        )

                        if any(
                            [
                                isinstance(new_spec, list),
                                isinstance(new_spec, tuple)
                            ]
                        ):
                            current_secret['distribute'].extend(new_spec)
                        else:
                            current_secret['distribute'].append(new_spec)

                    except InvalidSecretProvider as e:
                        LOGGER.warn(
                            'Cannot load provider "{}". Unable to distribute: '
                            '{}: {}'.format(target['provider'], target, e)
                        )

                        continue

            if current_secret['distribute']:
                filtered_secrets.append(current_secret)

        return filtered_secrets

    def load_secrets(self, rotate='nightly', secrets=None, batch_number=None, number_of_batches=None):
        LOGGER.info(
            'Attempting to load secrets ({}) from {}'.format(
                ', '.join(secrets) if secrets else 'ALL',
                self._config['provider']
            )
        )

        LOGGER.debug('Env config: {}'.format(self._config))

        config_provider = loader.build_client(self._config['provider'], None)
        config = config_provider.load_config(self._config['config'])

        self._validate_spec(*config)

        return self._filter(
            *config,
            rotate=rotate, requested_secrets=secrets, batch_number=batch_number, number_of_batches=number_of_batches)

    def get_accountusername(self):
        '''
        Get the account or organisation name of our chosen config provider

        :returns: Account or oganisation name from config provider
        :rtype: :class:`str`
        '''
        return self._config['config']['accountusername']
