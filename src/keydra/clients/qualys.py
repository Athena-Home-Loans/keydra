import requests
import xmltodict
from collections import OrderedDict


# https://www.qualys.com/platform-identification/
API_URL = {
    'US1': 'https://qualysapi.qualys.com',
    'US2': 'https://qualysapi.qg2.apps.qualys.com',
    'US3': 'https://qualysapi.qg3.apps.qualys.com',
    'EU1': 'https://qualysapi.qualys.eu',
    'EU2': 'https://qualysapi.qg2.apps.qualys.eu',
    'IN1': 'https://qualysapi.qg1.apps.qualys.in',
    'CA1': 'https://qualysapi.qg1.apps.qualys.ca',
    'AE1': 'https://qualysapi.qg1.apps.qualys.ae'
}


class ConnectionException(Exception):
    pass


class PasswordChangeException(Exception):
    pass


class QualysClient(object):
    def __init__(self, username, password, platform='US3', verify=True):
        '''
        Initializes a Qualys client

        :param username: Username used to connect
        :type username: :class:`string`
        :param password: Password to connect
        :type password: :class:`passwd`
        :param platform: The Qualys platform to use
        :type platform: :class:`string`, optional
        :param verify: Verify TLS
        :type verify: :class:`bool`
        '''

        self._baseurl = API_URL[platform]
        self._user = username
        self._pass = password

        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if type(self._user_list()) is not OrderedDict:
            raise ConnectionException('Unknown connection error')

    def _get(self, url, params=None):
        '''
        Send a GET request to the Qualys API.

        :param url: The URL to connect to, without the base
        :type url: :class:`string`
        :param params: The URL to connect to, without the base
        :type params: :class:`string`, optional

        :returns: Full API response
        :rtype: :class:`OrderedDict`
        '''

        api_url = '{}/{}'.format(self._baseurl, url)

        response = requests.request(
                "GET",
                api_url,
                headers=self._headers,
                params=params,
                auth=(self._user, self._pass)
            )
        error_msg = None

        if response.status_code == 200:
            respdict = xmltodict.parse(response.text)

            if not respdict.get('GENERIC_RETURN'):
                return respdict

            error_msg = respdict['GENERIC_RETURN']['RETURN']['#text']
        else:
            error_msg = '({}) {} '.format(
                str(response.status_code),
                response.text
            )

        raise ConnectionException(
            "Connection to {} with user '{}' failed: {}".format(
                api_url,
                self._user,
                error_msg
            )
        )

    def _user_list(self):
        '''
        Get a list of all current users.

        :returns: List of users
        :rtype: :class:`OrderedDict`
        '''

        return self._get(
            url='msp/user_list.php'
        )['USER_LIST_OUTPUT']['USER_LIST']

    def change_passwd(self, username):
        '''
        Update a Qualys user account password

        :param username: The username of the account
        :type username: :class:`string`

        :returns: The new password
        :rtype: :class:`string`
        '''

        params = {
            "email": "0",
            "user_logins": username
        }

        resp = self._get(
            url='/msp/password_change.php',
            params=params
        )['PASSWORD_CHANGE_OUTPUT']

        try:
            return(resp['RETURN']['CHANGES']['USER_LIST']['USER']['PASSWORD'])

        except Exception:
            raise PasswordChangeException(
                "Error '{}' changing '{}'s password - {}".format(
                    self._user,
                    username,
                    resp['RETURN']['MESSAGE']
                )
            )
