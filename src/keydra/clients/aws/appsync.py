import boto3

from botocore.exceptions import ClientError


class GetApiException(Exception):
    pass


class ListApiKeysException(Exception):
    pass


class CreateApiKeyException(Exception):
    pass


class DeleteApiKeyException(Exception):
    pass


class AppSyncClient:
    def __init__(self, session=None, region_name=None, **kwargs):
        if not session:
            session = boto3.session.Session()

        self._client = session.client(
            service_name='appsync',
            region_name=region_name
        )

    def list_api_keys(self, api_id, **kwargs):
        '''
        Lists all api keys for an existing app sync api

        :param api_id: ID (ARN or friendly api name) for the api
        :type api_id: :class:`str`
        :returns: the list of api keys for the api
        :rtype: :class:`dict`

        Sample response:
        {
            'apiKeys': [
                {
                    'id': 'string',
                    'description': 'string',
                    'expires': 123
                },
            ],
            'nextToken': 'string'
        }
        '''
        try:
            return self._client.list_api_keys(apiId=api_id, **kwargs)
        except ClientError as e:
            raise ListApiKeysException(
                'Error creating api key for app {}:'.format(api_id, e)
            )

    def create_api_key(self, api_id, expires, description):
        '''
        Creates an api key for an existing app sync api

        :param api_id: ID (ARN or friendly api name) for the api
        :type api_id: :class:`str`
        :param expires: Time after which the key expires
        :type expires: :class:`int`
        :param description: Key purpose description
        :type description: :class:`str`
        :returns: The newly created key
        :rtype: :class:`str`

        Sample response:
        {
            'apiKey': {
                'id': 'string',
                'description': 'string',
                'expires': 123
            }
        }
        '''
        try:
            return self._client.create_api_key(
                apiId=api_id,
                expires=expires,
                description=description
            )
        except ClientError as e:
            raise CreateApiKeyException(
                'Error creating api key for app {}:'.format(api_id, e)
            )

    def delete_api_key(self, api_id, id):
        '''
        Deletes an api key for an existing app sync api

        :param api_id: ID (ARN or friendly api name) for the api
        :type api_id: :class:`str`
        :param id: ID for api key
        :type id: :class:`str`
        :returns: {}
        :rtype: :class:`dict`

        Sample response:

        {}
        '''
        try:
            return self._client.delete_api_key(
                apiId=api_id,
                id=id
            )
        except ClientError as e:
            raise DeleteApiKeyException(
                'Error deleting api key {} for app {}:'.format(id, api_id, e)
            )

    def get_graphql_api(self, api_id):
        '''
        Gets an api hosted on app sync

        :param api_id: ID (ARN or friendly api name) for the api
        :type api_id: :class:`str`
        :returns: {}
        :rtype: :class:`dict`

        Sample response:

        {

            'graphqlApi': {
                'name': 'string',
                'apiId': 'string',
                'authenticationType': 'API_KEY',
                'logConfig': {
                    'fieldLogLevel': 'NONE'|'ERROR'|'ALL',
                    'cloudWatchLogsRoleArn': 'string',
                    'excludeVerboseContent': True|False
                },
                'userPoolConfig': {
                    'userPoolId': 'string',
                    'awsRegion': 'string',
                    'defaultAction': 'ALLOW'|'DENY',
                    'appIdClientRegex': 'string'
                },
                'openIDConnectConfig': {
                    'issuer': 'string',
                    'clientId': 'string',
                    'iatTTL': 123,
                    'authTTL': 123
                },
                'arn': 'string',
                'uris': {
                    'string': 'string'
                },
                'tags': {
                    'string': 'string'
                },
                'additionalAuthenticationProviders': [
                    {
                        'authenticationType': 'API_KEY'
                        'openIDConnectConfig': {
                            'issuer': 'string',
                            'clientId': 'string',
                            'iatTTL': 123,
                            'authTTL': 123
                        },
                        'userPoolConfig': {
                            'userPoolId': 'string',
                            'awsRegion': 'string',
                            'appIdClientRegex': 'string'
                        }
                    },
                ],
                'xrayEnabled': True|False,
                'wafWebAclArn': 'string'
            }
        }
        '''
        try:
            return self._client.get_graphql_api(
                apiId=api_id
            )
        except ClientError as e:
            raise GetApiException(
                'Error getting api with id {}: {}'.format(api_id, e)
            )
