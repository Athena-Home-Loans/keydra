import validators
import json

from simple_salesforce import Salesforce


class SalesforceClient(object):
    def __init__(self, username, password, token, domain):
        '''
        Initializes a Salesforce client

        :param username: Username used to connect
        :type username: :class:`string`
        :param password: Password used to connect
        :type password: :class:`passwd`
        :param token: Token used to connect
        :type token: :class:`passwd`
        :param domain: The domain to use
        :type domain: :class:`string`
        '''

        # We only use the domain if connecting to a sandbox
        if domain != "test":
            domain = None

        self._client = Salesforce(
                username=username,
                password=password,
                security_token=token,
                domain=domain
            )

        self._base_url = 'https://{}/services/data/v{}/sobjects'.format(
            self._client.sf_instance,
            self._client.sf_version
        )

    def get_user_id(self, username):
        '''
        Retrieves the Salesforce ID for a given
        username in the form of an email address.

        :param username: The username (email) to lookup
        :type app: :class:`string`

        :returns: The User ID corresponding to the username
        :rtype: :class:`string`
        '''
        # SQLi!
        if validators.email(username) is not True:
            raise ValidationException(
                'Username not an email address {} '.format(username))

        results = self._client.query(
            "SELECT name,id FROM User WHERE Username = '{0}'".format(username)
        )

        if results['totalSize'] == 1:
            # We only expect 1 result, any more is a fail
            return results['records'][0]['Id']
        else:
            raise Exception(
                'More than 1 search result {} {}'.format(username, results)
            )

    def change_passwd(self, userid, newpassword):
        '''
        Change a Salesforce user account password

        :param userid: The user ID of the account
        :type userid: :class:`string`
        :param newpasswd: The new password to change to
        :type newpasswd: :class:`passwd`

        :returns: True if successful
        :rtype: :class:`bool`
        '''
        url = (
            '{base}/User/{userid}/password'.format(
                base=self._base_url,
                userid=userid
            )
        )

        params = {'NewPassword': newpassword}

        result = self._client._call_salesforce(
            'POST',
            url,
            data=json.dumps(params)
        )

        # SF returns a 204 No Content when the request is successful
        if result.status_code != 200 and result.status_code != 204:
            raise Exception(
                'Failed to change password,  non 2XX result'
            )

        return True


class ValidationException(Exception):
    pass
