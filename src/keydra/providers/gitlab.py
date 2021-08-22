import copy
import json

import yaml
from schema import And, Optional, Or, Regex, Schema, SchemaError, Use

from keydra.clients.gitlab import GitlabClient
from keydra.exceptions import (ConfigException, DistributionException,
                               RotationException)
from keydra.logging import get_logger
from keydra.providers.base import (BaseProvider, ConfigProvider,
                                   exponential_backoff_retry)

LOGGER = get_logger()
SPEC_SCHEMA = Schema({'provider': 'gitlab',
                      'key': Regex(r'^[A-Za-z0-9_{}]{1,255}$'),
                      'source': And(str, Use(str.lower), lambda s: s in ('key', 'secret')),
                      'config': {
                          'repository': Or([And(str, len)], And(str, len)),
                          'scope': 'repository',
                          Optional('environment'): And(str, len)},
                      'envs': [And(str, len)]
                      })


class Client(BaseProvider):

    def __init__(self, session=None, credentials=None, **kwargs):
        self.repo_client = GitlabClient(
            access_token=credentials["access_token"]
        )

    def _distribute_repository_secret(self, secret, dest):
        config = dest['config']

        try:
            self.repo_client.set_repo_variable(
                repo_name=config['repository'],
                key=dest['key'],
                value=secret[dest['source']]
            )

        except Exception as e:  # pragma: no cover
            LOGGER.warn('Failed to distribute secret to Gitlab repo {}: {}'.format(
                config['repository'], e))
            raise DistributionException(e)

        LOGGER.info(
            'Successfully distributed {}.{}.key to '
            'gitlab.{}.{} '.format(
                secret['provider'],
                secret['key'],
                config['repository'],
                dest['key']
            )
        )

        return dest

    @classmethod
    def _validate_repository_spec(cls, spec):
        if 'repository' not in spec['config']:
            return False, 'Attribute "config.repository" not present'

        return True, ''

    def _distribute(self, secret, destination):
        try:
            # We only support repo level distribution right now
            return self._distribute_repository_secret(secret, destination)

        except Exception as e:
            raise DistributionException(e)

    def _load_as_dict_from_repo(self, file_path, repo_name, repo_branch, filetype):
        LOGGER.info(
            'Loading remote file from GitLab repo {} at path {}'.format(repo_name, file_path)
        )

        file_content = self.repo_client.fetch_file_from_repository(
            file_path=file_path,
            repo_name=repo_name,
            repo_branch=repo_branch
        )

        LOGGER.debug('Remote file content: \n{}'.format(file_content))

        if filetype.lower() in ['json']:
            return json.loads(file_content)
        elif filetype.lower() in ['yaml', 'yml']:
            return yaml.safe_load(file_content)
        else:
            raise ConfigException(
                'Unsupported filetype provided: {}'.format(filetype)
            )

    def load_config(self, config):
        cp = ConfigProvider(config)

        envs = self._load_as_dict_from_repo(
            file_path=cp.envs_path,
            repo_name=cp.envs_repo,
            repo_branch=cp.envs_repo_branch,
            filetype=cp.envs_filetype
        )

        secrets = self._load_as_dict_from_repo(
            file_path=cp.secrets_path,
            repo_name=cp.secrets_repo,
            repo_branch=cp.secrets_repo_branch,
            filetype=cp.secrets_filetype
        )

        return envs, secrets

    def rotate(self, secret):
        raise RotationException("Not implemented for GitLab")

    @ exponential_backoff_retry(3)
    def distribute(self, secret, destination):
        return self._distribute(secret, destination)

    @ classmethod
    def validate_spec(cls, spec):
        valid, msg = BaseProvider.validate_spec(spec)
        if not valid:
            return valid, msg

        try:
            SPEC_SCHEMA.validate(spec)
            return True, "Validation succeeded."
        except SchemaError as e:
            print(e)
            return False, str(e)

    @ classmethod
    def pre_process_spec(self, spec, context={}):
        # FIMXE
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
