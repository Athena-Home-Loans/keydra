import boto3

from keydra.providers.base import BaseProvider

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from datetime import datetime
from datetime import timedelta

from keydra.clients.aws.appsync import AppSyncClient
from keydra.clients.aws.appsync import CreateApiKeyException
from keydra.clients.aws.appsync import DeleteApiKeyException
from keydra.clients.aws.appsync import ListApiKeysException
from keydra.logging import get_logger
from keydra.providers.base import exponential_backoff_retry


TEMPLATE_FOR_KEY = 'km_managed_{}'


LOGGER = get_logger()


class Client(BaseProvider):
    def __init__(self, session=None, region_name=None, credentials=None):
        if session is None:
            session = boto3.session.Session()

        self._appsync_client = AppSyncClient(
            session=session,
            region_name=region_name
        )

    def _get_days_from_occurrence(self, occurrence):
        # TODO: Move to publicly accessible place
        return {
            'nightly': 5,
            'daily': 5,
            'weekly': 17,
            'monthly': 60
        }.get(occurrence, 30)

    def _generate_expiry_epoch(self, days_from_today):
        d = datetime.now() + timedelta(days=days_from_today)
        return int(d.timestamp())

    def _rotate(self, secret):
        existing_key = None
        target_key_description = TEMPLATE_FOR_KEY.format(secret['key'])
        api_id = secret['config']['api-id']
        occurrence = secret['rotate']
        days = self._get_days_from_occurrence(occurrence)
        expires_in = self._generate_expiry_epoch(days)
        try:
            for key in self._appsync_client.list_api_keys(api_id)['apiKeys']:
                if key.get('description') == target_key_description:
                    existing_key = key['id']
                    break
        except ListApiKeysException as e:
            LOGGER.error(
                'Unable to list key api keys for api {}.'.format(api_id)
            )
            raise RotationException(e)

        if existing_key is not None:
            try:
                self._appsync_client.delete_api_key(api_id, existing_key)
                LOGGER.info(
                    'api key {} for api {} deleted from appsync: {}'.format(
                        existing_key,
                        api_id
                    )
                )
            except DeleteApiKeyException as e:
                LOGGER.error(
                    'Unable to delete api key for api {}'.format(api_id)
                )
                raise RotationException(e)
        try:
            url = self._appsync_client.get_graphql_api(
                api_id
            )['graphqlApi']['uris']['GRAPHQL']

            result = self._appsync_client.create_api_key(
                api_id,
                expires_in,
                target_key_description
            )
            new_api_key = result['apiKey']
            LOGGER.info(
                    'new api key for api {} created in appsync: {}'.format(
                        target_key_description,
                        api_id
                    )
                )
            return {
                'provider': 'aws_appsync',
                'key': api_id,
                'secret': new_api_key['id'],
                'url': url
            }
        except CreateApiKeyException as e:
            LOGGER.error(
                'Unable to create api key for api {}'.format(api_id)
            )
            raise RotationException(e)

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate(secret)

    def distribute(self, secret, destination):
        raise DistributionException('AppSync does not support distribution')

    @classmethod
    def validate_spec(cls, spec):
        valid, msg = BaseProvider.validate_spec(spec)
        if not valid:
            return False, msg
        else:
            if 'config' in spec and 'api-id' in spec['config']:
                return True, 'All good!'
            else:
                return False, 'Please provide a config specifying the api-id'

    @classmethod
    def redact_result(cls, result):
        if 'value' in result and 'secret' in result['value']:
            result['value']['secret'] = '***'

        return result
