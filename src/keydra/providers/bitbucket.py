import copy
import json
import yaml

from keydra.clients.bitbucket import BitbucketClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import ConfigException
from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger


LOGGER = get_logger()

ACCT_USERNAME_TAG = 'account_username'


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None, **kwargs):
        self._client = BitbucketClient(
            user=credentials['username'],
            passwd=credentials['password']
        )

    def _distribute_account_secret(self, secret, dest):
        acct_username = dest['config'].get(ACCT_USERNAME_TAG)
        account_variables = self._client.list_team_pipeline_variables(
            username=acct_username
        )
        existing_variable = None

        for remote_var in account_variables:
            if remote_var['key'] == dest['key']:
                existing_variable = remote_var
                break

        try:
            if existing_variable is None:
                LOGGER.info(
                    '{} not present in Bitbucket[{}], adding.'.format(
                        dest['key'], 'ACCOUNT'
                    )
                )

                self._client.add_team_pipeline_variable(
                    key=dest['key'],
                    value=secret[dest['source']],
                    username=acct_username,
                    secured=True
                )

            else:
                LOGGER.info(
                    '{} is present in Bitbucket[{}], updating.'.format(
                        dest['key'], 'ACCOUNT'
                    )
                )

                self._client.update_team_pipeline_variable(
                    uuid=existing_variable['uuid'],
                    key=dest['key'],
                    value=secret[dest['source']],
                    username=acct_username,
                    secured=True
                )

        except Exception as e:  # pragma: no cover
            raise DistributionException(e)

        LOGGER.info(
            'Successfully distributed {}{} to Bitbucket[ACCOUNT] from '
            '{} - {}'.format(
                dest['key'],
                ' ({})'.format(secret['key']) if 'key' in secret else '',
                dest['source'],
                secret['provider']
            )
        )

        return dest

    def _get_or_create_environment(self, config):
        environment = config.get('environment', '').lower()

        repo_envs_by_slug = {
            x['slug']: x
            for x in self._client.list_repo_environments(
                config['repository'],
                username=config[ACCT_USERNAME_TAG]
            )
        }

        environment = config.get('mapping', {}).get(
            environment, environment
        ).lower()

        if environment not in repo_envs_by_slug:
            if config.get('create', False) is False:
                raise DistributionException(
                    'Environment with slug "{}" not present in Bitbucket for '
                    'repo: {} and is not configured to create. Aborting!'
                    .format(environment, config['repository'])
                )

            LOGGER.info(
                'Environment with slug "{}" not present in Bitbucket for '
                'repo: {}, attempting to create!'.format(
                    environment, config['repository'])
            )

            new_env = self._client.add_repo_environment(
                repo_slug=config['repository'],
                name=environment,
                username=config[ACCT_USERNAME_TAG],
                env_type='Production'
            )

            repo_envs_by_slug[new_env['slug']] = new_env

        env_uuid = repo_envs_by_slug.get(environment)['uuid']

        if not env_uuid:  # pragma: no cover
            raise DistributionException(
                'Not able to get (or create) environment "{}" under "{}" '
                .format(environment, config['repository'])
            )

        return env_uuid, environment

    def _distribute_deployment_secret(self, secret, dest):
        config = dest['config']

        env_uuid, environment = self._get_or_create_environment(
            config
        )

        env_vars = self._client.list_repo_deployment_variables(
            repo_slug=config['repository'],
            env_uuid=env_uuid,
            username=config[ACCT_USERNAME_TAG]
        )
        existing_variable = None

        for remote_var in env_vars:
            if remote_var['key'] == dest['key']:
                existing_variable = remote_var
                break

        try:
            if existing_variable is None:
                LOGGER.info(
                    '{} not present in Bitbucket[{}::{}], adding.'.format(
                        dest['key'], config['repository'], environment
                    )
                )

                self._client.add_repo_deployment_variable(
                    repo_slug=config['repository'],
                    env_uuid=env_uuid,
                    key=dest['key'],
                    value=secret[dest['source']],
                    username=config[ACCT_USERNAME_TAG],
                    secured=True
                )

            else:
                LOGGER.info(
                    '{} is present in Bitbucket[{}::{}], updating.'.format(
                        dest['key'], config['repository'], environment
                    )
                )

                self._client.update_repo_deployment_variable(
                    var_uuid=existing_variable['uuid'],
                    repo_slug=config['repository'],
                    env_uuid=env_uuid,
                    key=dest['key'],
                    value=secret[dest['source']],
                    username=config[ACCT_USERNAME_TAG],
                    secured=True
                )

        except Exception as e:  # pragma: no cover
            raise DistributionException(e)

        LOGGER.info(
            'Successfully distributed {}{} to Bitbucket[{}::{}] from '
            '{} - {}'.format(
                dest['key'],
                ' ({})'.format(secret['key']) if 'key' in secret else '',
                dest['source'],
                secret['provider'],
                config['repository'],
                environment
            )
        )

        return dest

    def _distribute_repository_secret(self, secret, dest):
        config = dest['config']

        env_vars = self._client.list_repo_variables(
            config['repository'],
            username=config[ACCT_USERNAME_TAG]
        )
        existing_variable = None

        for remote_var in env_vars:
            if remote_var['key'] == dest['key']:
                existing_variable = remote_var
                break

        try:
            if existing_variable is None:
                LOGGER.info(
                    '{} not present in Bitbucket[{}], adding.'.format(
                        dest['key'], config['repository']
                    )
                )

                if not dest['source'] in secret:
                    raise DistributionException(
                        'Key "{}" not found in the secret'.format(
                            dest['source']))

                self._client.add_repo_variable(
                    repo_slug=config['repository'],
                    key=dest['key'],
                    value=secret[dest['source']],
                    username=config[ACCT_USERNAME_TAG],
                    secured=True
                )

            else:
                LOGGER.info(
                    '{} is present in Bitbucket[{}], updating.'.format(
                        dest['key'], config['repository']
                    )
                )

                self._client.update_repo_variable(
                    var_uuid=existing_variable['uuid'],
                    repo_slug=config['repository'],
                    key=dest['key'],
                    value=secret[dest['source']],
                    username=config[ACCT_USERNAME_TAG],
                    secured=True
                )

        except Exception as e:  # pragma: no cover
            LOGGER.warn('Failed to distribute secret: {}'.format(e))
            raise DistributionException(e)

        LOGGER.info(
            'Successfully distributed {}{} to Bitbucket[{}] from '
            '{} - {}'.format(
                dest['key'],
                ' ({})'.format(secret['key']) if 'key' in secret else '',
                dest['source'],
                secret['provider'],
                config['repository'],
            )
        )

        return dest

    def rotate(self, secret):
        raise RotationException('Bitbucket provider does not support rotation')

    def _distribute(self, secret, destination):
        try:
            if destination['scope'] == 'account':
                return self._distribute_account_secret(secret, destination)

            elif destination['scope'] == 'repository':
                return self._distribute_repository_secret(secret, destination)

            elif destination['scope'] == 'deployment':
                return self._distribute_deployment_secret(secret, destination)

            else:
                raise NotImplementedError(
                    'Bitbucket for scope {}'.format(destination['scope'])
                )

        except Exception as e:
            raise DistributionException(e)

    @exponential_backoff_retry(3)
    def distribute(self, secret, destination):
        return self._distribute(secret, destination)

    @classmethod
    def _validate_repository_spec(cls, spec):
        if 'repository' not in spec['config']:
            return False, 'Attribute "config.repository" not present'

        return True, ''

    @classmethod
    def _validate_deployment_spec(cls, spec):
        for attribute in ['repository', 'environment']:
            if attribute not in spec['config']:
                return False, 'Attribute "config.{}" not present'.format(
                    attribute
                )

        return True, ''

    @classmethod
    def validate_spec(cls, spec):
        valid, msg = BaseProvider.validate_spec(spec)

        if not valid:
            return valid, msg

        if 'scope' not in spec:
            return False, 'Attribute "scope" not present in configuration'

        if 'config' not in spec:
            return False, 'Attribute "config" not present in configuration'

        if spec['scope'] == 'deployment':
            return Client._validate_deployment_spec(spec)

        if spec['scope'] == 'repository':
            return Client._validate_repository_spec(spec)

        return True, 'It is valid!'  # pragma: no cover

    @classmethod
    def pre_process_spec(self, spec, context={}):
        specs = []

        target = copy.deepcopy(spec)

        current_env_name, current_env = list(
            context.get('environment', {}).items()
        )[0]

        if 'ENV' in target['key']:
            target['key'] = target['key'].format(
                **{'ENV': current_env_name.upper()}
            )

        if 'ENV' in target.get('config', {}).get(
            'environment', ''
        ):
            target['config']['environment'] = target[
                'config'
            ]['environment'].format(
                **{'ENV': current_env_name.upper()}
            )

        if spec['scope'] in ['deployment', 'repository'] and any(
            [
                isinstance(spec['config']['repository'], list),
                isinstance(spec['config']['repository'], tuple)
            ]
        ):
            for repo in spec['config']['repository']:
                new_target = copy.deepcopy(target)
                new_target['config']['repository'] = repo

                specs.append(new_target)
        else:
            specs.append(target)

        return specs

    def _load_remote_file(self, repo, path, username, filetype):
        LOGGER.info(
            'Loading remote file: {} - {}'.format(repo, path)
        )

        resp = self._client.fetch_file_from_repository(
            repo=repo,
            path=path,
            username=username
        )

        LOGGER.debug('Remove file content: \n{}'.format(resp))

        if filetype.lower() in ['json']:
            return json.loads(resp)

        elif filetype.lower() in ['yaml', 'yml']:
            return yaml.safe_load(resp)

        else:
            raise ConfigException(
                'Unsupported filetype provided: {}'.format(filetype)
            )

    def load_config(self, config):
        username = config.get('accountusername')
        secrets_repo = config.get('secrets', {}).get('repository')
        secrets_path = config.get('secrets', {}).get('path')
        secrets_filetype = config.get('secrets', {}).get('filetype', 'yaml')
        envs_repo = config.get('environments', {}).get('repository')
        envs_path = config.get('environments', {}).get('path')
        envs_filetype = config.get('environments', {}).get('filetype', 'yaml')

        if not secrets_repo:
            raise ConfigException(
                '"repository" not defined for "secrets" in configuration'
            )

        if not envs_repo:
            raise ConfigException(
                '"repository" not defined for "environments" in configuration'
            )

        if not username:
            raise ConfigException(
                '"accountusername" not defined in configuration'
            )

        LOGGER.info('Attempting to load config from Bitbucket')

        envs = self._load_remote_file(
            repo=envs_repo,
            path=envs_path,
            filetype=envs_filetype,
            username=username
        )

        specs = self._load_remote_file(
            repo=secrets_repo,
            path=secrets_path,
            filetype=secrets_filetype,
            username=username
        )

        return envs, specs
