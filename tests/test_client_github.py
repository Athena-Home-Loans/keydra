import unittest
import requests
import json

from unittest.mock import patch
from unittest.mock import MagicMock


from keydra.clients import github


PUBKEY = {
  "key_id": "012345678912345678",
  "key": "2Sg8iYjAxxmI2LvUXpJjkYrMxURPc8rrewgfvghwevg="
}


class TestGithubClient(unittest.TestCase):
    def test__init(self):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )

        self.assertEqual(
            cli._authorizer,
            {
                'Content-Type': 'application/json',
                'Authorization': 'token secret'
            }
        )

    def test__get_pubkey(self):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )
        cli._query = MagicMock()
        cli._query.return_value = json.dumps(PUBKEY)

        self.assertEqual(cli._get_repo_public_key('org', 'repo'), PUBKEY)

    def test__encrypt(self):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )

        self.assertEqual(
            cli._encrypt_secret(secret='test', public_key=PUBKEY).endswith('=='),
            True
        )

    def test__add_repo_variable(self):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )
        cli._get_repo_public_key = MagicMock()
        cli._get_repo_public_key.return_value = PUBKEY

        cli._encrypt_secret = MagicMock()
        cli._encrypt_secret.return_value = 'oooh..secret!'

        cli._put = MagicMock()

        cli.add_repo_variable(repo='repo', key='name', value='pass', org='org')
        cli._put.assert_called_once_with(
            'https://api.github.com/repos/org/repo/actions/secrets/name',
            json={
                'key_id': '012345678912345678',
                'encrypted_value': 'oooh..secret!'
            }
        )

    @patch.object(github.requests, 'put')
    def test__put(self, mk_put):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )

        mk_put().text = {'test': 'response'}
        self.assertEqual(cli._put(url='test', json={}), {'test': 'response'})

    @patch.object(github.requests, 'get')
    def test__get(self, mk_get):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )
        mk_get().text = {'test': 'response'}
        self.assertEqual(cli._query(url='test'), {'test': 'response'})

    @patch.object(github.requests, 'post')
    def test__post(self, mk_post):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )
        mk_post().text = {'test': 'response'}
        self.assertEqual(cli._post(url='test'), {'test': 'response'})

    @patch.object(github.requests, 'delete')
    def test__delete(self, mk_del):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )
        mk_del().status_code = 200
        mk_del().text = {'status': 200, 'text': 'woot'}
        self.assertEqual(
            cli._delete(url='test'), {'status': 200, 'text': 'woot'}
        )

    @patch.object(github.requests, 'get')
    def test__list_repo_variables(self, mk_get):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )
        mk_get().text = {
            "total_count": 2,
            "secrets": [
              {
                "name": "GH_TOKEN",
                "created_at": "2019-08-10T14:59:22Z",
                "updated_at": "2020-01-10T14:59:22Z"
              },
              {
                "name": "GIST_ID",
                "created_at": "2020-01-10T10:59:22Z",
                "updated_at": "2020-01-11T11:59:22Z"
              }
            ]
        }

        self.assertEqual(
            cli.list_repo_variables(repo='repo', org='org'),
            [
                {
                    "name": "GH_TOKEN",
                    "created_at": "2019-08-10T14:59:22Z",
                    "updated_at": "2020-01-10T14:59:22Z"
                },
                {
                    "name": "GIST_ID",
                    "created_at": "2020-01-10T10:59:22Z",
                    "updated_at": "2020-01-11T11:59:22Z"
                }
            ]
        )

    @patch.object(github.requests, 'get')
    @patch.object(github.requests, 'post')
    @patch.object(github.requests, 'delete')
    def test__authfail(self, mk_del, mk_post, mk_get):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )
        mock_resp = requests.models.Response()
        mock_resp.status_code = 401

        mk_del.return_value = mock_resp
        mk_get.return_value = mock_resp
        mk_post.return_value = mock_resp

        with self.assertRaises(Exception):
            cli._delete(url='test')

        with self.assertRaises(Exception):
            cli._get(url='test')

        with self.assertRaises(Exception):
            cli._post(url='test')

    @patch.object(github.requests, 'get')
    def test__fetch_file_from_repository(self, mk_get):
        cli = github.GithubClient(
            user='username',
            passwd='secret'
        )
        mk_get().text = {'woot': 'yeah'}
        self.assertEqual(
            cli.fetch_file_from_repository(
                org='org',
                repo='repo',
                path='path'
            ),
            {'woot': 'yeah'}
        )
