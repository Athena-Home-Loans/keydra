import unittest

from unittest.mock import MagicMock
from unittest.mock import patch

import splunklib.client as splunkclient
from splunklib.binding import HTTPError

from keydra.clients.splunk import SplunkClient
from keydra.clients.splunk import AppNotInstalledException

SPLUNK_CREDS = {
    "provider": "splunk",
    "key": "admin_key",
    "secret": "test"
}


class body():
    def __init__(self, text):
        self.text = text

    def read(self):
        return self.text


class response():
    def __init__(self, status, body, reason='', headers=''):
        self.status = status
        self.reason = reason
        self.body = body
        self.headers = headers


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

        with self.assertRaises(AppNotInstalledException):
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
        httpResponse = response(
            status=200, reason="does not exist", body=body('does not exist')
        )
        httpResponse2 = response(
            status=800, reason="does not exist", body=body('does not exist')
        )

        sp_client._service.post(
            '/servicesNS/nobody/app/path/obj', name='obj'
        ).side_effect = HTTPError(httpResponse)
        sp_client._service.post.return_value = httpResponse2

        result = sp_client.update_app_config('app', 'path', 'obj', dict())

        self.assertEqual(result, 800)

    @patch.object(splunkclient, 'HTTPError')
    @patch.object(splunkclient, 'Service')
    def test__update_app_obj_error(self, mk_splunk, mk_error):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']
        httpResponse = response(status=404, body=body("wooty tooty"))
        sp_client._service.post.side_effect = HTTPError(httpResponse)

        with self.assertRaises(Exception):
            sp_client.update_app_config('app', 'path', 'obj', dict())

    @patch.object(splunkclient, 'HTTPError')
    @patch.object(splunkclient, 'Service')
    def test__storepass_fail(self, mk_splunk, mk_error):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']
        sp_client._service.get.return_value.status = 200

        httpResponse = response(status=200, reason="no!", body=body(''))
        sp_client._service.post().side_effect = HTTPError(httpResponse)

        sp_client._service.post.return_value = None

        with self.assertRaises(Exception):
            print(sp_client.update_app_storepass(
                app='app',
                username='user',
                password='pass',
                realm='test'
            ))

    @patch.object(splunkclient, 'Service')
    def test__storepass_exists(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']
        sp_client._service.get.return_value.status = 200
        sp_client._service.post.return_value.status = 200

        u_result = sp_client.update_app_storepass(
            app='app',
            username='user',
            password='pass'
        )

        self.assertEqual(u_result, 200)

    @patch.object(splunkclient, 'Service')
    def test__storepass_notexist(self, mk_splunk):
        sp_client = SplunkClient(
                username=SPLUNK_CREDS['key'],
                password=SPLUNK_CREDS['secret'],
                host='127.0.0.1',
                verify=False
            )
        sp_client._service.apps.list.return_value = ['app']
        httpResponse = response(status=200, reason="no!", body=body(''))
        sp_client._service.post().side_effect = HTTPError(httpResponse)
        sp_client._service.post.return_value.status = 200

        u_result = sp_client.update_app_storepass(
            app='app',
            username='user',
            password='pass'
        )

        self.assertEqual(u_result, 200)

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

        httpResponse = response(status=200, reason="no!", body=body(''))
        sp_client._service.post().side_effect = HTTPError(httpResponse)

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

        httpResponse = response(
            status=200, reason="no!", body=body('does not exist')
        )
        sp_client._service.post().side_effect = HTTPError(httpResponse)

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
