import unittest
import requests

from unittest.mock import patch

from keydra.clients import bitbucket


class TestGithubClient(unittest.TestCase):
    def test__init(self):
        cli = bitbucket.BitbucketClient(
            user='username',
            passwd='secret'
        )
        self.assertEqual(
            type(cli._authorizer),
            requests.auth.HTTPBasicAuth
        )

    @patch.object(bitbucket.requests, 'put')
    def test__put(self, mk_put):
        cli = bitbucket.BitbucketClient(
            user='username',
            passwd='secret'
        )

        mk_put().json.return_value = {'test': 'response'}
        self.assertEqual(cli._put(url='test', json={}), {'test': 'response'})

    @patch.object(bitbucket.requests, 'get')
    def test__get(self, mk_get):
        cli = bitbucket.BitbucketClient(
            user='username',
            passwd='secret'
        )
        mk_get().json.return_value = {'test': 'response'}
        self.assertEqual(cli._query(url='test'), {'test': 'response'})

    @patch.object(bitbucket.requests, 'post')
    def test__post(self, mk_post):
        cli = bitbucket.BitbucketClient(
            user='username',
            passwd='secret'
        )
        mk_post().json.return_value = {'test': 'response'}
        self.assertEqual(cli._post(url='test'), {'test': 'response'})

    @patch.object(bitbucket.requests, 'delete')
    def test__delete(self, mk_del):
        cli = bitbucket.BitbucketClient(
            user='username',
            passwd='secret'
        )
        mk_del().status_code = 200
        mk_del().text = {'status': 200, 'text': 'woot'}
        self.assertEqual(
            cli._delete(url='test'), {'status': 200, 'text': {'status': 200, 'text': 'woot'}}
        )
