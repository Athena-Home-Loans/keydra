import json
import time
import math

from abc import ABC
from abc import abstractmethod


def exponential_backoff_retry(attempts, delay=2):
    '''
    Retries execution while it throws exceptions for the amount of times
    set up.

    When giving up, re-raises the original exception.

    :param attemps: Number of attempts before giving up
    :type attempts: :class:`int`
    :param delay: Number of seconds to delay before retrying
    :type delay: :class:`int`
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
                    t_attempts -= 1
                    time.sleep(t_delay)
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
