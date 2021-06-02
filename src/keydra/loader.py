import boto3
import json

from botocore.exceptions import ClientError

from importlib import import_module
import inspect

from keydra import logging as km_logging

from keydra.clients.aws.secretsmanager import SecretsManagerClient

from keydra.exceptions import ConfigException, InvalidSecretProvider

from keydra.providers.base import BaseProvider


DEFAULT_REGION_NAME = 'ap-southeast-2'

# Global variables are reused across execution contexts (if available)
SESSION = boto3.Session()

KEYDRA_SECRETS_PREFIX = 'keydra'

SECRETS_MANAGER = SecretsManagerClient(region_name=DEFAULT_REGION_NAME)

LOCAL_PROVIDERS = {
    'appsync': 'aws_appsync',
    'iam': 'aws_iam',
    'secretsmanager': 'aws_secretsmanager'
}

LOCAL_CLIENTS = {
    'appsync': 'aws.appsync',
    'iam': 'aws.iam',
    'secretsmanager': 'aws.secretsmanager'
}

LOGGER = km_logging.get_logger()


def fetch_provider_creds(provider, key_name):
    secret_value = None

    secret_id = '{}/{}'.format(KEYDRA_SECRETS_PREFIX, provider.lower())

    if key_name:
        secret_id = '{}/{}'.format(secret_id, key_name)

    try:
        LOGGER.debug('Loading {} from Secrets Manager'.format(secret_id))
        secret_value = SECRETS_MANAGER.get_secret_value(secret_id)
    except ClientError as e:  # pragma: no cover
        LOGGER.debug(
            'Not able to read credentials for: {} -- {}'.format(provider, e))
        raise ConfigException(
            'Failed to read {} from Secrets Manager: {}'.format(
                secret_id, e))

    try:
        LOGGER.debug('Attempting to convert secret to JSON')
        return json.loads(secret_value)
    except Exception as e:
        LOGGER.debug('Failed converting {} to JSON: {}'.format(secret_id, e))
        raise ConfigException(
            'The value of {} is not valid JSON'.format(secret_id))


def load_provider_client(secret_provider):
    try:
        sanitized_provider = secret_provider.lower()
        module_name = 'keydra.providers.{}'.format(
            LOCAL_PROVIDERS.get(sanitized_provider, sanitized_provider)
        )
        module = import_module(module_name)

        providers = []
        for _, obj in inspect.getmembers(module):
            if (inspect.isclass(obj)
                    and issubclass(obj, BaseProvider)
                    and obj != BaseProvider):
                providers.append(obj)

        if len(providers) == 0:
            raise AttributeError(
                'Didn\'t find any classes extending BaseProvider in {}'
                .format(module_name)
            )

        if len(providers) > 1:
            raise AttributeError(
                'Found multiple classes extending BaseProvider in {}'
                .format(module_name)
            )

        return providers[0]

    except (ModuleNotFoundError, AttributeError) as e:
        raise InvalidSecretProvider(
            'Secret Provider for "{}" is not available: {}'.format(
                secret_provider, e
            )
        )


def load_client(provider):
    try:
        sanitized_provider = provider.lower()
        module_name = 'keydra.clients.{}'.format(
            LOCAL_CLIENTS.get(sanitized_provider, sanitized_provider)
        )
        module = import_module(module_name)

        providers = []
        for _, obj in inspect.getmembers(module):
            if _.endswith('Client'):
                providers.append(obj)

        if len(providers) == 0:
            raise AttributeError(
                'Didn\'t find any classes extending object in {}'
                .format(module_name)
            )

        if len(providers) > 1:
            raise AttributeError(
                'Found multiple classes extending object in {}'
                .format(module_name)
            )

        return providers[0]

    except (ModuleNotFoundError, AttributeError) as e:
        raise InvalidSecretProvider(
            'Client for "{}" is not available: {}'.format(
                provider, e
            )
        )


def build_client(secret_provider, key_name):
    km_provider = load_provider_client(secret_provider)
    credentials = None
    if km_provider.has_creds():
        credentials = fetch_provider_creds(secret_provider, key_name)
    else:
        LOGGER.debug('Don\'t need to fetch creds for ' + secret_provider)

    return km_provider(
        session=SESSION,
        credentials=credentials,
        region_name=DEFAULT_REGION_NAME
    )
