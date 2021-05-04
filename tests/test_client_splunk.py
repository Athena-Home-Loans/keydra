import unittest

from unittest.mock import MagicMock
from unittest.mock import patch

import splunklib.client as splunkclient

from keydra.clients.splunk import SplunkClient

SPLUNK_CREDS = {
    "provider": "splunk",
    "key": "admin_key",
    "secret": "test"
}


class HTTPError(Exception):
    """This exception is raised for HTTP responses that return an error."""
    def __init__(self, body):
        self.body = body


class TestSplunkClient(unittest.TestCase):
    @patch.object(splunkclient, 'Service')
    def test__splunk_init(self,  mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )

        sp_client._service.login.assert_called_once_with()

    @patch.object(splunkclient, 'Service')
    def test__update_app_not_installed(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )

        sp_client._service.apps.list.return_value = []

        with self.assertRaises(Exception):
            sp_client.update_app_config('app', 'path', 'obj', dict())

    @patch.object(splunkclient, 'Service')
    def test__update_app_installed(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )

        sp_client._service.apps.list.return_value = ['app']
        sp_client.update_app_config('app', 'path', 'obj', dict())

        sp_client._service.apps.list.assert_called_once_with(search='name=app')

    @patch.object(splunkclient, 'HTTPError')
    @patch.object(splunkclient, 'Service')
    def test__update_app_obj_not_exist(self, mk_splunk, mk_error):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']
        sp_client.update_app_config('app', 'path', 'obj', dict())

        sp_client._service.post().side_effect = Exception(
            splunkclient.HTTPError()
        )

        self.assertEqual(sp_client._service.post.call_count, 2)

    @patch.object(splunkclient, 'Service')
    def test__update_app_obj_exists(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']
        sp_client._service.post.return_value.status = 200

        u_result = sp_client.update_app_config('app', 'path', 'obj', dict())

        self.assertEqual(u_result, 200)

    @patch.object(splunkclient, 'Service')
    def test__update_app_fail_400(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']
        sp_client._service.post.return_value.status = 400

        u_result = sp_client.update_app_config('app', 'path', 'obj', dict())
        self.assertEqual(u_result, 400)

    @patch.object(splunkclient, 'Service')
    def test__update_app_fail_except(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']
        sp_client._service.post.side_effect = Exception()

        with self.assertRaises(Exception):
            sp_client.update_app_config('app', 'path', 'obj', dict())

    @patch.object(splunkclient, 'HTTPError')
    @patch.object(splunkclient, 'Service')
    def test__update_app_bad_input(self, mk_splunk, mk_error):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']

        sp_client._service.post().side_effect = HTTPError(body="")

        with self.assertRaises(Exception):
            sp_client.update_app_config('app', 'path', 'obj', "dict")

    @patch.object(splunkclient, 'Service')
    def test__update_app_create_fail(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._app_exists = MagicMock()
        sp_client._app_exists.return_value = True
        sp_client._service.post.side_effect = Exception(
            HTTPError(body="does not exist")
        )

        with self.assertRaises(Exception):
            sp_client.update_app_config('app', 'path', 'obj', "dict")

    @patch.object(splunkclient, 'Service')
    def test__change_pass(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )

        sp_client._service.post.return_value.status = 200
        c_result = sp_client.change_passwd('admin', 'old', 'new')

        sp_client._service.post.assert_called_once_with(
            '/services/authentication/users/admin',
            oldpassword='old',
            password='new'
        )
        self.assertEqual(c_result, True)

    @patch.object(splunkclient, 'Service')
    def test__change_pass_fail(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )

        sp_client._service.post.return_value.status = 400

        with self.assertRaises(Exception):
            sp_client.change_passwd('admin', 'old', 'new')
