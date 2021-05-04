from keydra.clients.cloudflare import CloudflareClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger


LOGGER = get_logger()


class CloudflareException(Exception):
    pass


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None, **kwargs):
        self._credentials = credentials
        self._client = CloudflareClient(credentials['manage_tokens.secret'])

    def _rotate(self, secret):
        resp = self._credentials
        resp['provider'] = 'cloudflare'

        if secret is None:
            secret = 'all'

        try:
            if self._client.verify().get('success') is not True:
                raise CloudflareException(
                    'Not able to verify token in Cloudflare'
                )

            tokens_by_name = {
                x['name']: x for x in self._client.list_tokens()['result']
            }

            if not tokens_by_name:
                raise CloudflareException('No tokens found in Cloudflare')

            for token_name, token in tokens_by_name.items():
                if secret != 'all' and secret != token_name:
                    LOGGER.debug(
                        'Ignoring token "{}" for not being selected for '
                        'rotation'.format(token_name)
                    )

                    continue

                new_secret = self._client.roll_token(token['id'])

                if new_secret.get('success') is not True:
                    raise CloudflareException(
                        'Error rotating secret for: {} ({}) -> {}'.format(
                            token['name'], token['id'], new_secret['errors']
                        )
                    )
                else:
                    LOGGER.info(
                        'Token {} ({}) rotated successfully'.format(
                            token['name'], token['id']
                        )
                    )

                token_key = '{}.key'.format(token['name'])
                token_secret = '{}.secret'.format(token['name'])

                resp[token_key] = token['id']
                resp[token_secret] = new_secret['result']

            LOGGER.info(
                'Rotated all {} Cloudflare tokens successfully'.format(
                    len(tokens_by_name)
                )
            )

        except Exception as e:
            raise RotationException(e)

        return resp

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate(secret.get('key'))

    def distribute(self, secret, destination):
        raise DistributionException(
            'Cloudflare provider does not support distribution'
        )

    @classmethod
    def redact_result(cls, result):
        if 'value' in result:
            for key, value in result['value'].items():
                if 'secret' in key:
                    result['value'][key] = '***'

        return result
