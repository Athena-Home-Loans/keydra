import unittest

from keydra.providers import cloudflare

from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch


CF_CREDS = {'manage_tokens.secret': 'pass'}


CF_SECRET_ALL = {
    'key': 'all',
    'provider': 'cloudflare',
}

CF_SECRET_ALL = {
    'key': 'all',
    'provider': 'cloudflare',
}


class TestProviderCloudflare(unittest.TestCase):
    def test_distribute(self):
        cli = cloudflare.Client(credentials=CF_CREDS)

        with self.assertRaises(DistributionException):
            cli.distribute('bla', 'somewhere')

    @patch.object(cloudflare.Client, '_rotate')
    def test_rotate(self, mk_r):
        cli = cloudflare.Client(credentials=CF_CREDS)

        cli.rotate({'key': 'all'})

        mk_r.assert_called_once_with('all')

    def test__rotate_bad_verify(self):
        cli = cloudflare.Client(credentials=CF_CREDS)
        cli._client = MagicMock()
        cli._client.verify.return_value = {'success': False}

        with self.assertRaises(RotationException):
            cli._rotate('all')

        cli._client.verify.side_effect = Exception('Boom')

        with self.assertRaises(RotationException):
            cli._rotate('all')

    def test__rotate_bad_list_tokens(self):
        cli = cloudflare.Client(credentials=CF_CREDS)
        cli._client = MagicMock()
        cli._client.verify.return_value = {'success': True}
        cli._client.list_tokens.return_value = {'result': []}

        with self.assertRaises(RotationException):
            cli._rotate('all')

        cli._client.list_tokens.side_effect = Exception('Boom')

        with self.assertRaises(RotationException):
            cli._rotate('all')

    def test__rotate_bad_roll_token(self):
        cli = cloudflare.Client(credentials=CF_CREDS)
        cli._client = MagicMock()
        cli._client.verify.return_value = {'success': True}
        cli._client.list_tokens.return_value = {
            'result': [{'id': 'id', 'name': 'name'}]
        }
        cli._client.roll_token.return_value = {'success': False}

        with self.assertRaises(RotationException):
            cli._rotate('all')

        cli._client.roll_token.side_effect = Exception('Boom')

        with self.assertRaises(RotationException):
            cli._rotate('all')

    def test__rotate(self):
        cli = cloudflare.Client(credentials=CF_CREDS)
        cli._client = MagicMock()
        cli._client.verify.return_value = {'success': True}
        cli._client.roll_token.return_value = {
            'result': 'some_secret',
            'success': True
        }
        cli._client.list_tokens.return_value = {
            'result': [
                {
                    'id': 'd475f3be504dd5ba4b290018180fe64c',
                    'name': 'manage_dns',
                    'status': 'active',
                    'issued_on': '2020-05-12T01:07:02Z',
                    'modified_on': '2020-05-12T01:07:02Z',
                    'last_used_on': None,
                    'policies': []
                },
                {
                    'id': '0e64546b0b4d554208f7bc1435c7dcc9',
                    'name': 'manage_tokens',
                    'status': 'active',
                    'issued_on': '2020-05-12T00:47:52Z',
                    'modified_on': '2020-05-12T01:06:08Z',
                    'last_used_on': '2020-05-12T03:19:22Z',
                    'policies': []
                }
            ],
            'result_info': {
                'page': 1,
                'per_page': 20,
                'total_pages': 1,
                'count': 2,
                'total_count': 2
            },
            'success': True,
            'errors': [],
            'messages': []
        }

        resp = cli._rotate('manage_tokens')

        self.assertEqual(
            resp,
            {
                'provider': 'cloudflare',
                'manage_tokens.key': '0e64546b0b4d554208f7bc1435c7dcc9',
                'manage_tokens.secret': 'some_secret',
            }
        )

        cli._client.roll_token.assert_called_once_with(
            '0e64546b0b4d554208f7bc1435c7dcc9'
        )

        cli._client.roll_token.reset_mock()
        resp = cli._rotate('all')

        self.assertEqual(
            resp,
            {
                'provider': 'cloudflare',
                'manage_tokens.key': '0e64546b0b4d554208f7bc1435c7dcc9',
                'manage_tokens.secret': 'some_secret',
                'manage_dns.key': 'd475f3be504dd5ba4b290018180fe64c',
                'manage_dns.secret': 'some_secret',
            }
        )
        cli._client.roll_token.assert_has_calls(
            [
                call('d475f3be504dd5ba4b290018180fe64c'),
                call('0e64546b0b4d554208f7bc1435c7dcc9'),
            ]
        )

        cli._client.roll_token.reset_mock()
        resp = cli._rotate(None)

        self.assertEqual(
            resp,
            {
                'provider': 'cloudflare',
                'manage_tokens.key': '0e64546b0b4d554208f7bc1435c7dcc9',
                'manage_tokens.secret': 'some_secret',
                'manage_dns.key': 'd475f3be504dd5ba4b290018180fe64c',
                'manage_dns.secret': 'some_secret',
            }
        )
        cli._client.roll_token.assert_has_calls(
            [
                call('d475f3be504dd5ba4b290018180fe64c'),
                call('0e64546b0b4d554208f7bc1435c7dcc9'),
            ]
        )

    def test_redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'manage_tokens.secret': 'SECRET_ONE',
                'provider': 'cloudflare',
                'manage_dns.key': 'd475f3be504dd5ba4b290018180fe64c',
                'manage_dns.secret': 'SECRET_TWO',
                'manage_tokens.key': '0e64546b0b4d554208f7bc1435c7dcc9'
            }
        }

        r_result = cloudflare.Client.redact_result(result)
        r_value = r_result['value']

        self.assertNotEqual(r_value['manage_tokens.secret'], 'SECRET_ONE')
        self.assertNotEqual(r_value['manage_dns.secret'], 'SECRET_TWO')
