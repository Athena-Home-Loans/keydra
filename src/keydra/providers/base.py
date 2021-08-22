import json
import time
import math
import random

from abc import ABC
from abc import abstractmethod

from keydra.exceptions import ConfigException


def exponential_backoff_retry(attempts, delay=2, max_random=3, exception_type=None):
    '''
    Retries execution while it throws exceptions for the amount of times
    set up. Adds some randomness to the delay each time.

    When giving up, re-raises the original exception.

    :param attempts: Number of attempts before giving up
    :type attempts: :class:`int`
    :param delay: Number of seconds to delay before retrying
    :type delay: :class:`int`
    :param max_random: Maximum number of extra seconds to add to the delay
    :type max_random: :class:`int`
    :param exception_type: Optional, only retry is exception thrown is of this type
    :type exception_type: :class:`class`
    :returns: original return of invoked function or method
    '''
    attempts = math.floor(attempts)

    def decorator(f):
        def retry(*args, **kwargs):
            t_attempts = attempts
            t_delay = delay
            exc = None

            while t_attempts >= 0:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    exc = e

                    if exception_type and not isinstance(e, exception_type):
                        break

                    t_attempts -= 1
                    time.sleep(t_delay + random.randint(0, max_random))
                    t_delay *= delay

            if exc:
                raise exc

        return retry
    return decorator


class BaseProvider(ABC):
    @abstractmethod
    def rotate(self, key):
        pass

    @abstractmethod
    def distribute(self, secret, key):
        pass

    def load_config(self, config):
        raise NotImplementedError(
            '{} does not implement "load_config"'.format(
                self.__class__.__name__
            )
        )

    @classmethod
    def pre_process_spec(cls, spec, context={}):
        return spec

    @classmethod
    def validate_spec(cls, spec):
        missing_keys = []
        required_keys = ['provider', 'key']

        for key in required_keys:
            if key not in spec:
                missing_keys.append(key)

        if missing_keys:
            return False, 'Invalid spec. Missing keys: {} for {}'.format(
                ', '.join(missing_keys), json.dumps(spec, indent=2)
            )

        return True, 'All good!'

    @classmethod
    def redact_result(self, result):
        return result

    @classmethod
    def has_creds(cls):
        return True


class ConfigProvider(ABC):
    '''
    Standardised Config Provider class. Takes in config and validates

    :param config: Keydra config provider config.
    :type config: :class:`dict`
    '''

    ACCOUNTUSERNAME = 'accountusername'
    SECRETS = 'secrets'
    SECRETS_FILETYPE = 'filetype'
    SECRETS_REPO = 'repository'
    SECRETS_REPO_BRANCH = 'repositorybranch'
    SECRETS_PATH = 'path'
    ENVS = 'environments'
    ENVS_FILETYPE = 'filetype'
    ENVS_REPO = 'repository'
    ENVS_REPO_BRANCH = 'repositorybranch'
    ENVS_PATH = 'path'

    def __init__(self, config):
        self.username = config.get(self.ACCOUNTUSERNAME)
        self.secrets_repo = config.get(self.SECRETS, {}).get(self.SECRETS_REPO)
        self.secrets_repo_branch = config.get(self.SECRETS, {}).get(self.SECRETS_REPO_BRANCH)
        self.secrets_path = config.get(self.SECRETS, {}).get(self.SECRETS_PATH)
        self.secrets_filetype = config.get(self.SECRETS, {}).get(self.SECRETS_FILETYPE, 'yaml')
        self.envs_repo = config.get(self.ENVS, {}).get(self.ENVS_REPO)
        self.envs_repo_branch = config.get(self.ENVS, {}).get(self.ENVS_REPO_BRANCH)
        self.envs_path = config.get(self.ENVS, {}).get(self.ENVS_PATH)
        self.envs_filetype = config.get(self.ENVS, {}).get(self.ENVS_FILETYPE, 'yaml')

        if not self.secrets_repo:
            raise ConfigException(
                '"{}" not defined for "{}" in configuration'.format(
                    self.SECRETS_REPO,
                    self.SECRETS
                )
            )

        if not self.envs_repo:
            raise ConfigException(
                '"{}" not defined for "{}" in configuration'.format(
                    self.ENVS_REPO,
                    self.ENVS
                )
            )

        if not self.username:
            raise ConfigException(
                '"{}" not defined in configuration'.format(
                    self.ACCOUNTUSERNAME
                )
            )
