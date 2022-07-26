import copy
import json
import yaml

from keydra.clients.github import GithubClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import ConfigProvider

from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import ConfigException
from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger


LOGGER = get_logger()

ACCT_USERNAME_TAG = 'account_username'


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None, **kwargs):
        self._client = GithubClient(
            user=credentials['username'],
            passwd=credentials['password']
        )
        self.accountusername = None

    def _distribute_repository_secret(self, secret, dest):
        config = dest['config']

        if ACCT_USERNAME_TAG in config:
            # Account/org is being over-ridden
            org = config.get(ACCT_USERNAME_TAG)
        else:
            org = self.accountusername

        try:
            self._client.add_repo_variable(
                repo=config['repository'],
                key=dest['key'],
                value=secret[dest['source']],
                org=org
            )

        except Exception as e:  # pragma: no cover
            LOGGER.warn('Failed to distribute secret to Github repo {}: {}'.format(
                    config['repository'],
                    e
                )
            )
            raise DistributionException(e)

        LOGGER.info(
            'Successfully distributed {}.{}.key to '
            'github.{}.{} '.format(
                secret['provider'],
                secret['key'],
                config['repository'],
                dest['key']
            )
        )

        return dest

    def rotate(self, secret):
        raise RotationException('Github provider does not support rotation')

    def _distribute(self, secret, destination):
        try:
            # We only support repo level distribution right now
            return self._distribute_repository_secret(secret, destination)

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
    def validate_spec(cls, spec):
        valid, msg = BaseProvider.validate_spec(spec)

        if not valid:
            return valid, msg

        if 'config' not in spec:
            return False, 'Attribute "config" not present in configuration'

        if 'scope' not in spec['config']:
            return False, 'Attribute "scope" not present in configuration'

        if spec['config']['scope'] != 'repository':
            return False, 'Unsupported scope'
        else:
            return Client._validate_repository_spec(spec)

    @classmethod
    def pre_process_spec(self, spec, context: dict):
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

        if spec['config']['scope'] in ['deployment', 'repository'] and any(
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
            'Loading remote file from Github repo {} at path {}'.format(repo, path)
        )

        resp = self._client.fetch_file_from_repository(
            repo=repo,
            path=path,
            org=username
        )

        LOGGER.debug('Remote file content: \n{}'.format(resp))

        if filetype.lower() in ['json']:
            return json.loads(resp)

        elif filetype.lower() in ['yaml', 'yml']:
            return yaml.safe_load(resp)

        else:
            raise ConfigException(
                'Unsupported filetype provided: {}'.format(filetype)
            )

    def load_config(self, config):
        Cp = ConfigProvider(config)

        LOGGER.info('Attempting to load config from Github')

        envs = self._load_remote_file(
            repo=Cp.envs_repo,
            path=Cp.envs_path,
            filetype=Cp.envs_filetype,
            username=Cp.username
        )

        specs = self._load_remote_file(
            repo=Cp.secrets_repo,
            path=Cp.secrets_path,
            filetype=Cp.secrets_filetype,
            username=Cp.username
        )

        return envs, specs
