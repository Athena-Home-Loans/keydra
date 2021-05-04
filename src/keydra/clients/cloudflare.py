import requests


API_URL = 'https://api.cloudflare.com/client/v4'
API_TOKENS = '{}/user/tokens'.format(API_URL)


class CloudflareClient(object):
    def __init__(self, token_secret):
        '''
        Initializes a client for Cloudflare

        :param token_secret: Secret for Token in Cloudflare
        :type token_secret: :class:`passwd`
        '''
        self._token_secret = token_secret
        self._auth_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(token_secret)
        }

    def _query(self, url):
        resp = requests.get(url, headers=self._auth_headers)

        resp.raise_for_status()

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _post(self, url, **kwargs):
        resp = requests.post(url, headers=self._auth_headers, **kwargs)

        resp.raise_for_status()

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _put(self, url, **kwargs):
        resp = requests.put(url, headers=self._auth_headers, **kwargs)

        resp.raise_for_status()

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _delete(self, url):
        resp = requests.delete(url, headers=self._auth_headers)

        resp.raise_for_status()

        return {'status': resp.status_code, 'text': resp.text}

    def verify(self):
        '''
        Tests a token

        :returns: Information about the operation (as per Cloudflare's
            description)
        :rtype: :class:`dict`
        '''
        url = '{}/verify'.format(API_TOKENS)

        return self._query(url)

    def details(self, token_id):
        '''
        Reveals details about the token.

        :param token_id: ID of the token details should be provided for
        :type token_id: :class:`str`
        :returns: Information about the operation (as per Cloudflare's
            description)
        :rtype: :class:`dict`
        '''
        url = '{}/{}'.format(API_TOKENS, token_id)

        return self._query(url)

    def list_tokens(self):
        '''
        List available tokens

        :returns: Information about the operation (as per Cloudflare's
            description)
        :rtype: :class:`list` of :class:`dict`
        '''
        url = API_TOKENS

        return self._query(url)

    def roll_token(self, token_id):
        '''
        Rolls the token, generating a new one

        :returns: Information about the operation (as per Cloudflare's
            description)
        :rtype: :class:`dict`
        '''
        url = '{}/{}/value'.format(API_TOKENS, token_id)

        return self._put(url, data={})
