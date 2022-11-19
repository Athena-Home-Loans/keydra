from keydra.clients.contentful import ContentfulClient

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from keydra.logging import get_logger

LOGGER = get_logger()

PW_FIELD = 'secret'


class Client(BaseProvider):
    def __init__(self, session=None, credentials=None, region_name=None):
        self._secret_key = credentials['key']
        self._cfclient = ContentfulClient(token=credentials[PW_FIELD])

    def _rotate_secret(self, secret):
        try:
            curr_tokens = self._cfclient.get_tokens()

            new_token = self._cfclient.create_token(
                name=self._secret_key,
                readonly=False
            )

        except Exception as error:
            LOGGER.error(
                "Failed to rotate Contentful token '{}' - {}".format(
                    self._secret_key,
                    error
                )
            )
            raise RotationException(
                'Error rotating token {} on Contentful - '
                'error : {}'.format(
                    self._secret_key,
                    error
                )
            )

        try:
            # Revoke all existing tokens, just leaving our new one
            for token in curr_tokens:
                self._cfclient.revoke_token(token_id=token.id)

        except Exception as error:
            LOGGER.error(
                'Failed to revoke Contentful token'
            )
            raise RotationException(
                'Error revoking token on Contentful - '
                'error : {}'.format(
                    error
                )
            )

        LOGGER.info(
            "Contentful token '{}' successfully rotated.".format(
                self._secret_key
            )
        )

        return {
            'provider': 'contentful',
            'key': self._secret_key,
            f'{PW_FIELD}': new_token.token,
        }

    @exponential_backoff_retry(3)
    def rotate(self, secret):
        return self._rotate_secret(secret)

    def distribute(self, secret, destination):
        raise DistributionException('Contentful does not support distribution')
