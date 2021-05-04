import copy
import unittest

from keydra.providers import bitbucket

from keydra.exceptions import ConfigException
from keydra.exceptions import DistributionException
from keydra.exceptions import RotationException

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch


BB_CREDS = {'username': 'user', 'password': 'pass'}


IAM_SECRET = {
    'key': 'secret_key',
    'secret': 'secret_secret',
    'provider': 'iam'
}

BB_DEST_ACCT = {
    'key': 'secret_name',
    'provider': 'bitbucket',
    'source': 'key',
    'scope': 'account',
    'envs': ['*'],
    'config': {'account_username': 'acct_user'}
}

BB_DEST_REPO = {
    'key': 'secret_name',
    'provider': 'bitbucket',
    'source': 'key',
    'scope': 'repository',
    'config': {'repository': 'repo', 'account_username': 'acct_user'},
    'envs': ['*']
}

BB_DEST_ENV = {
    'key': 'secret_name',
    'provider': 'bitbucket',
    'source': 'key',
    'scope': 'deployment',
    'config': {
        'repository': 'repo',
        'environment': 'env',
        'account_username': 'acct_user',
        'create': True
    },
    'envs': ['*']
}

BB_DEST_REPO_NO_CREATE = {
    'key': 'secret_name',
    'provider': 'bitbucket',
    'source': 'key',
    'scope': 'repository',
    'config': {
        'repository': 'repo',
        'environment': 'env',
        'account_username': 'acct_user',
        'create': False
    },
    'envs': ['*']
}

BB_DEST_ENV_MULTI_REPO = {
    'key': 'secret_name_{ENV}',
    'provider': 'bitbucket',
    'source': 'key',
    'scope': 'deployment',
    'config': {
        'repository': ['repoA', 'repoB'],
        'environment': '{ENV}',
        'account_username': 'acct_user'
    },
    'envs': ['*']
}


class TestProviderBitbucket(unittest.TestCase):
    def test__distribute_account_secret_new_var(self):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.list_team_pipeline_variables.return_value = []

        cli._distribute_account_secret(IAM_SECRET, BB_DEST_ACCT)

        cli._client.add_team_pipeline_variable.assert_called_once_with(
            key='secret_name',
            value='secret_key',
            username='acct_user',
            secured=True
        )

    def test__distribute_account_secret_existing_var(self):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.list_team_pipeline_variables.return_value = [
            {'key': 'secret_name', 'uuid': 'uuid'}
        ]

        cli._distribute_account_secret(IAM_SECRET, BB_DEST_ACCT)

        cli._client.update_team_pipeline_variable.assert_called_once_with(
            uuid='uuid',
            key='secret_name',
            value='secret_key',
            username='acct_user',
            secured=True
        )

    def test__distribute_repo_secret_new_var(self):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.list_repo_variables.return_value = []

        cli._distribute_repository_secret(IAM_SECRET, BB_DEST_REPO)

        cli._client.add_repo_variable.assert_called_once_with(
            repo_slug='repo',
            key='secret_name',
            value='secret_key',
            username='acct_user',
            secured=True
        )

    def test__distribute_repo_secret_existing_var(self):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.list_repo_variables.return_value = [
            {'key': 'secret_name', 'uuid': 'uuid'}
        ]

        cli._distribute_repository_secret(IAM_SECRET, BB_DEST_REPO)

        cli._client.update_repo_variable.assert_called_once_with(
            repo_slug='repo',
            var_uuid='uuid',
            key='secret_name',
            value='secret_key',
            username='acct_user',
            secured=True
        )

    @patch.object(bitbucket.Client, '_get_or_create_environment')
    def test__distribute_deployment_secret_new_var(self, mk_goce):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.list_repo_deployment_variables.return_value = []
        mk_goce.return_value = ['env_uuid', 'env']

        cli._distribute_deployment_secret(IAM_SECRET, BB_DEST_ENV)

        cli._client.add_repo_deployment_variable.assert_called_once_with(
            env_uuid='env_uuid',
            repo_slug='repo',
            key='secret_name',
            value='secret_key',
            username='acct_user',
            secured=True
        )

    @patch.object(bitbucket.Client, '_get_or_create_environment')
    def test__distribute_deployment_secret_existing_var(self, mk_goce):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.list_repo_deployment_variables.return_value = [
            {'key': 'secret_name', 'uuid': 'uuid'}
        ]
        mk_goce.return_value = ['env_uuid', 'env']

        cli._distribute_deployment_secret(IAM_SECRET, BB_DEST_ENV)

        cli._client.update_repo_deployment_variable.assert_called_once_with(
            env_uuid='env_uuid',
            repo_slug='repo',
            var_uuid='uuid',
            key='secret_name',
            value='secret_key',
            username='acct_user',
            secured=True
        )

    def test__get_or_create_environment_existing_env(self):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.list_repo_environments.return_value = [
            {'slug': 'env', 'uuid': 'uuid'}
        ]

        env_uuid, env = cli._get_or_create_environment(BB_DEST_ENV['config'])

        cli._client.add_repo_environment.assert_not_called()

        self.assertEqual(env_uuid, 'uuid')
        self.assertEqual(env, 'env')

    def test__get_or_create_environment_new_env(self):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.list_repo_environments.return_value = []
        cli._client.add_repo_environment.return_value = {
            'slug': 'env', 'uuid': 'uuid'
        }

        env_uuid, env = cli._get_or_create_environment(BB_DEST_ENV['config'])

        cli._client.add_repo_environment.assert_called_once_with(
            repo_slug='repo',
            name='env',
            env_type='Production',
            username='acct_user'
        )

        self.assertEqual(env_uuid, 'uuid')
        self.assertEqual(env, 'env')

        with self.assertRaises(DistributionException):
            cli._get_or_create_environment(BB_DEST_REPO_NO_CREATE['config'])

    def test_rotate(self):
        cli = bitbucket.Client(credentials=BB_CREDS)

        with self.assertRaises(RotationException):
            cli.rotate(IAM_SECRET)

    @patch.object(bitbucket.Client, '_distribute_account_secret')
    @patch.object(bitbucket.Client, '_distribute_repository_secret')
    @patch.object(bitbucket.Client, '_distribute_deployment_secret')
    def test_distribute(self, mk_dds, mk_drs, mk_das):
        cli = bitbucket.Client(credentials=BB_CREDS)

        cli._distribute(IAM_SECRET, BB_DEST_ACCT)

        mk_das.assert_called_once_with(IAM_SECRET, BB_DEST_ACCT)

        cli._distribute(IAM_SECRET, BB_DEST_REPO)

        mk_das.assert_called_once_with(IAM_SECRET, BB_DEST_ACCT)

        cli._distribute(IAM_SECRET, BB_DEST_ENV)

        mk_das.assert_called_once_with(IAM_SECRET, BB_DEST_ACCT)

    def test_distribute_unknown_scope(self):
        cli = bitbucket.Client(credentials=BB_CREDS)

        with self.assertRaises(DistributionException):
            cli._distribute(IAM_SECRET, {'scope': 'not_supported'})

    def test__validate_repository_spec(self):
        valid, _ = bitbucket.Client._validate_repository_spec(
            {'config': {}}
        )

        self.assertEqual(valid, False)

        valid, _ = bitbucket.Client._validate_repository_spec(
            {'config': {'repository': 'repo'}}
        )

        self.assertEqual(valid, True)

    def test__validate_deployment_spec(self):
        valid, _ = bitbucket.Client._validate_deployment_spec(
            {'config': {}}
        )

        self.assertEqual(valid, False)

        valid, _ = bitbucket.Client._validate_deployment_spec(
            {'config': {'repository': 'repo'}}
        )

        self.assertEqual(valid, False)

        valid, _ = bitbucket.Client._validate_deployment_spec(
            {'config': {'repository': 'repo', 'environment': 'env'}}
        )

        self.assertEqual(valid, True)

    @patch('keydra.providers.bitbucket.Client._validate_repository_spec')
    @patch('keydra.providers.bitbucket.Client._validate_deployment_spec')
    @patch('keydra.providers.base.BaseProvider.validate_spec')
    def test_validate_spec(self, mk_bvc, mk_vdc, mk_vrc):
        mk_bvc.return_value = [True, '']

        valid, _ = bitbucket.Client.validate_spec({})

        self.assertEqual(valid, False)

        valid, _ = bitbucket.Client.validate_spec(
            {
                'scope': 'deployment'
            }
        )

        self.assertEqual(valid, False)

        mk_vrc.return_value = [True, '']
        valid, _ = bitbucket.Client.validate_spec(
            {
                'scope': 'repository',
                'config': {}
            }
        )

        self.assertEqual(valid, True)
        mk_vrc.assert_called()

        mk_vdc.return_value = [True, '']
        valid, _ = bitbucket.Client.validate_spec(
            {
                'scope': 'deployment',
                'config': {}
            }
        )

        self.assertEqual(valid, True)
        mk_vdc.assert_called()

        mk_bvc.return_value = [False, '']
        valid, _ = bitbucket.Client.validate_spec(
            {
                'scope': 'deployment',
                'config': {}
            }
        )

        self.assertEqual(valid, False)

    def test_pre_process_spec(self):
        targets = bitbucket.Client.pre_process_spec(
            BB_DEST_ENV_MULTI_REPO,
            context={'environment': {'dev': None}}
        )

        exp_target_a = copy.deepcopy(BB_DEST_ENV_MULTI_REPO)
        exp_target_a['key'] = 'secret_name_DEV'
        exp_target_a['config']['repository'] = 'repoA'
        exp_target_a['config']['environment'] = 'DEV'

        exp_target_b = copy.deepcopy(BB_DEST_ENV_MULTI_REPO)
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
        cli = bitbucket.Client(credentials=BB_CREDS)
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
            username='username'
        )

    def test__load_remote_file_yaml(self):
        cli = bitbucket.Client(credentials=BB_CREDS)
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
            username='username'
        )

    def test__load_remote_file_unexpected_format(self):
        cli = bitbucket.Client(credentials=BB_CREDS)
        cli._client = MagicMock()
        cli._client.fetch_file_from_repository.return_value = 'stuff'

        with self.assertRaises(ConfigException):
            cli._load_remote_file(
                repo='repo',
                path='path',
                username='username',
                filetype='something'
            )

    @patch('keydra.providers.bitbucket.Client._load_remote_file')
    def test_load_config(self, lrf):
        cli = bitbucket.Client(credentials=BB_CREDS)
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
