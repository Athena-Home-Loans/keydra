from contentful_management import Client
from contentful_management import array


class ContentfulClient(object):
    def __init__(self, token):
        '''
        Initializes a Contentful client

        :param token: Token used to connect
        :type token: :class:`string`
        '''

        self._client = Client(
            access_token=token
        )
        self._validate_client()

    def _validate_client(self):
        '''
        Validate we have a working API connection
        and access to at least one space
        '''
        spaces = self._client.spaces().all()

        if type(spaces) is not array.Array:
            raise ConnectionException(
                'Could not connect to Contentful API!'
            )

    def get_tokens(self):
        '''
        Get a list of the current tokens

        :returns: List of tokens
        :rtype: :class:`list`
        '''
        return self._client.personal_access_tokens().all()

    def create_token(self, name, readonly=True):
        '''
        Create a new personal access token

        :param name: Token name
        :type name: :class:`string`
        :param readonly: True for Read Only access, default True
        :type level: :class:`bool`

        :returns: New token
        :rtype: :class:
            `contentful_management.personal_access_token.PersonalAccessToken`
        '''

        scope = 'content_management_read' if readonly \
            else 'content_management_manage'

        new_pa_token = self._client.personal_access_tokens().create(
            {
                'name': name,
                'scopes': [scope]
            }
        )
        return new_pa_token

    def revoke_token(self, token_id):
        '''
        Revoke a token with a specified ID

        :param token_id: The ID of the token to revoke
        :type app: :class:`string`

        :returns: True if successful, False otherwise
        :rtype: :class:`bool`
        '''
        r_result = self._client.personal_access_tokens().revoke(
            token_id
        )
        return r_result


class ConnectionException(Exception):
    pass


class ParameterException(Exception):
    pass
