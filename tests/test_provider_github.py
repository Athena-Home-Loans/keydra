import copy
import unittest

from keydra.providers import github

from keydra.exceptions import ConfigException
from keydra.exceptions import RotationException

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch


GH_CREDS = {'username': 'user', 'password': 'pass'}


IAM_SECRET = {
    'key': 'secret_key',
    'secret': 'secret_secret',
    'provider': 'iam'
}

GH_DEST_ACCT = {
    'key': 'secret_name',
    'provider': 'github',
    'source': 'key',
    'envs': ['*'],
    'config': {
        'account_username': 'acct_user',
        'scope': 'account'
    }
}

GH_DEST_REPO = {
    'key': 'secret_name',
    'provider': 'github',
    'source': 'key',
    'config': {
        'repository': 'repo',
        'scope': 'repository'
    },
    'envs': ['*']
}

GH_DEST_REPO_OVERRIDE = {
    'key': 'secret_name',
    'provider': 'github',
    'source': 'key',
    'config': {
        'repository': 'repo',
        'account_username': 'acct_user',
        'scope': 'repository'
    },
    'envs': ['*']
}

GH_DEST_ENV = {
    'key': 'secret_name',
    'provider': 'github',
    'source': 'key',
    'config': {
        'repository': 'repo',
        'environment': 'env',
        'account_username': 'acct_user',
        'create': True,
        'scope': 'deployment'
    },
    'envs': ['*']
}

GH_DEST_ENV_MULTI_REPO = {
    'key': 'secret_name_{ENV}',
    'provider': 'github',
    'source': 'key',
    'config': {
        'repository': ['repoA', 'repoB'],
        'environment': '{ENV}',
        'account_username': 'acct_user',
        'scope': 'deployment'
    },
    'envs': ['*']
}


class TestProviderGithub(unittest.TestCase):
    def test__distribute_repo_secret_new_var(self):
        cli = github.Client(credentials=GH_CREDS)

        cli._client = MagicMock()
        cli._client.list_repo_variables.return_value = []

        cli._distribute_repository_secret(IAM_SECRET, GH_DEST_REPO)

        cli._client.add_repo_variable.assert_called_once_with(
            repo='repo',
            key='secret_name',
            value='secret_key',
            org=None
        )

    def test__distribute_repo_secret_existing_var(self):
        cli = github.Client(credentials=GH_CREDS)

        cli._client = MagicMock()
        cli._client.list_repo_variables.return_value = [
            {'name': 'secret_name'}
        ]

        cli._distribute_repository_secret(IAM_SECRET, GH_DEST_REPO)

        cli._client.add_repo_variable.assert_called_once_with(
            repo='repo',
            key='secret_name',
            value='secret_key',
            org=None
        )

    def test__distribute_repo_override_org(self):
        cli = github.Client(credentials=GH_CREDS)

        cli._client = MagicMock()
        cli._client.list_repo_variables.return_value = [
            {'name': 'secret_name'}
        ]

        cli._distribute_repository_secret(IAM_SECRET, GH_DEST_REPO_OVERRIDE)

        cli._client.add_repo_variable.assert_called_once_with(
            repo='repo',
            key='secret_name',
            value='secret_key',
            org='acct_user'
        )

    def test_rotate(self):
        cli = github.Client(credentials=GH_CREDS)

        with self.assertRaises(RotationException):
            cli.rotate(IAM_SECRET)

    @patch.object(github.Client, '_distribute_repository_secret')
    def test_distribute(self, mk_drs):
        cli = github.Client(credentials=GH_CREDS)

        cli._distribute(IAM_SECRET, GH_DEST_REPO)
        mk_drs.assert_called_once_with(IAM_SECRET, GH_DEST_REPO)

    def test__validate_repository_spec(self):
        valid, _ = github.Client._validate_repository_spec(
            {'config': {}}
        )

        self.assertEqual(valid, False)

        valid, _ = github.Client._validate_repository_spec(
            {'config': {'repository': 'repo'}}
        )

        self.assertEqual(valid, True)

    @patch('keydra.providers.github.Client._validate_repository_spec')
    @patch('keydra.providers.base.BaseProvider.validate_spec')
    def test_validate_spec(self, mk_bvc, mk_vrc):
        mk_bvc.return_value = [True, '']

        valid, _ = github.Client.validate_spec({})
        self.assertEqual(valid, False)

        valid, _ = github.Client.validate_spec(
            {
                'scope': 'deployment'
            }
        )
        self.assertEqual(valid, False)

        mk_vrc.return_value = [True, '']
        valid, _ = github.Client.validate_spec(
            {
                'config': {
                    'repository': 'woot',
                    'scope': 'repository'
                }
            }
        )

        self.assertEqual(valid, True)
        mk_vrc.assert_called()

        mk_bvc.return_value = [False, '']
        valid, _ = github.Client.validate_spec(
            {
                'scope': 'deployment',
                'config': {}
            }
        )

        self.assertEqual(valid, False)

    def test_pre_process_spec(self):
        targets = github.Client.pre_process_spec(
            GH_DEST_ENV_MULTI_REPO,
            context={'environment': {'dev': None}}
        )

        exp_target_a = copy.deepcopy(GH_DEST_ENV_MULTI_REPO)
        exp_target_a['key'] = 'secret_name_DEV'
        exp_target_a['config']['repository'] = 'repoA'
        exp_target_a['config']['environment'] = 'DEV'

        exp_target_b = copy.deepcopy(GH_DEST_ENV_MULTI_REPO)
        exp_target_b['key'] = 'secret_name_DEV'
        exp_target_b['config']['repository'] = 'repoB'
        exp_target_b['config']['environment'] = 'DEV'

        self.assertEqual(len(targets), 2)
        self.assertIn(targets[0]['config']['repository'], ['repoA', 'repoB'])
        self.assertIn(targets[1]['config']['repository'], ['repoA', 'repoB'])
        self.assertEqual(targets[0]['key'], 'secret_name_DEV')
        self.assertEqual(targets[1]['key'], 'secret_name_DEV')
        self.assertEqual(targets[0]['config']['environment'], 'DEV')
        self.assertEqual(targets[1]['config']['environment'], 'DEV')

    def test__load_remote_file_json(self):
        cli = github.Client(credentials=GH_CREDS)
        cli._client = MagicMock()
        cli._client.fetch_file_from_repository.return_value = '{"json":"yes"}'

        resp = cli._load_remote_file(
            repo='repo',
            path='path',
            username='username',
            filetype='json'
        )

        self.assertEqual(resp, {'json': 'yes'})

        cli._client.fetch_file_from_repository.assert_called_with(
            repo='repo',
            path='path',
            org='username'
        )

    def test__load_remote_file_yaml(self):
        cli = github.Client(credentials=GH_CREDS)
        cli._client = MagicMock()
        cli._client.fetch_file_from_repository.return_value = '{"yaml":"yes"}'

        resp = cli._load_remote_file(
            repo='repo',
            path='path',
            username='username',
            filetype='yaml'
        )

        self.assertEqual(resp, {'yaml': 'yes'})

        cli._client.fetch_file_from_repository.assert_called_with(
            repo='repo',
            path='path',
            org='username'
        )

    def test__load_remote_file_unexpected_format(self):
        cli = github.Client(credentials=GH_CREDS)
        cli._client = MagicMock()
        cli._client.fetch_file_from_repository.return_value = 'stuff'

        with self.assertRaises(ConfigException):
            cli._load_remote_file(
                repo='repo',
                path='path',
                username='username',
                filetype='something'
            )

    @patch('keydra.providers.github.Client._load_remote_file')
    def test_load_config(self, lrf):
        cli = github.Client(credentials=GH_CREDS)
        cli._client = MagicMock()
        lrf.side_effect = ['a', 'b']

        with self.assertRaises(ConfigException):
            cli.load_config({})

        with self.assertRaises(ConfigException):
            cli.load_config({'accountusername': 'acct_user'})

        with self.assertRaises(ConfigException):
            cli.load_config({'secrets': {'repo': 'repo'}})

        with self.assertRaises(ConfigException):
            cli.load_config({'environments': {'repo': 'repo'}})

        resp = cli.load_config(
            {
                'accountusername': 'acct_user',
                'secrets': {
                    'repository': 'secrets_repo',
                    'path': 'secrets_path',
                },
                'environments': {
                    'repository': 'env_repo',
                    'path': 'env_path',
                }
            }
        )

        lrf.assert_has_calls(
            [
                call(
                    repo='env_repo',
                    path='env_path',
                    username='acct_user',
                    filetype='yaml'
                ),
                call(
                    repo='secrets_repo',
                    path='secrets_path',
                    username='acct_user',
                    filetype='yaml'
                ),
            ]
        )

        self.assertEqual(resp, ('a', 'b'))
