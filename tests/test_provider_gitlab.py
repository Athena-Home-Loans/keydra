import json
import unittest
from unittest.mock import MagicMock, call, patch

import yaml
from keydra.exceptions import ConfigException, DistributionException
from keydra.providers.gitlab import Client

A_BRANCH_NAME = "my-feature/my-branch"
A_FILE_PATH = "path/to/a.file"
A_FILE_TYPE = "atype"
A_REPO_NAME = "my-group/my-repo"
ANOTHER_BRANCH_NAME = "your-feature/your-branch"
ANOTHER_FILE_PATH = "path/to/another.file"
ANOTHER_FILE_TYPE = "anothertype"
ANOTHER_REPO_NAME = "your-group/your-repo"

IAM_SECRET = {
    'key': 'secret_key',
    'secret': 'secret_secret',
    'provider': 'iam'
}

GL_DEST_REPO = {
    'key': 'secret_name',
    'provider': 'github',
    'source': 'key',
    'config': {
        'repository': 'repo',
        'scope': 'repository'
    },
    'envs': ['*']
}

VALID_CONFIG = {
    'accountusername': 'dummy',
    'secrets': {
        'repository': A_REPO_NAME,
        'repositorybranch': A_BRANCH_NAME,
        'path': A_FILE_PATH,
        'filetype': A_FILE_TYPE,
    },
    'environments': {
        'repository': ANOTHER_REPO_NAME,
        'repositorybranch': ANOTHER_BRANCH_NAME,
        'path': ANOTHER_FILE_PATH,
        'filetype': ANOTHER_FILE_TYPE,
    }
}

VALID_PROVIDER_SPEC = {
    'provider': 'gitlab',
    'config': {'repository': 'mygroup/myrepo',
               'scope': 'repository'},
    'key': 'AWS_ACCESS_KEY_ID',
    'source': 'key',
    'envs': ['*']
}

VALID_PROVIDER_SPEC_MULTI_REPOS = {
    'provider': 'gitlab',
    'config': {'repository': ['mygroup/myrepo', 'myothergroup/myotherrepo'],
               'scope': 'repository',
               'environment': '{ENV}'},
    'key': 'secret_name_{ENV}',
    'source': 'key',
    'envs': ['*']
}

INVALID_PROVIDER_SPEC = {
    'provider': 'gitlab',
    'config': {},
    'key': 'AWS_ACCESS_KEY_ID',
    'source': 'key',
    'envs': ['*']
}


class TestProviderGitlab(unittest.TestCase):

    def setUp(self):
        self.client = Client.__new__(Client)
        self.client.repo_client = MagicMock()

    def test__should_set_repo_var_on_distribute_repository_secret(self):
        self.client._distribute_repository_secret(IAM_SECRET, GL_DEST_REPO)

        self.client.repo_client.set_repo_variable.assert_called_once_with(
            key='secret_name', repo_name='repo', value='secret_key')

    def test__should_raise_exception_if_cannot_distribute_secret(self):
        self.client.repo_client.set_repo_variable.side_effect = Exception('Not a good day')

        with self.assertRaises(DistributionException):
            self.client._distribute_repository_secret(IAM_SECRET, GL_DEST_REPO)

    def test__should_validate_valid_repo_spec(self):
        result, _ = self.client._validate_repository_spec(GL_DEST_REPO)

        assert result

    def test__should_validate_invalid_repo_spec(self):
        result, _ = self.client._validate_repository_spec({'config': []})

        assert not result

    @patch.object(Client, '_distribute_repository_secret', side_effect=Exception('Not a good day'))
    def test__should_raise_distribution_exception_on_distribution_problems(self, mock_drs):
        with self.assertRaises(DistributionException):
            self.client._distribute(IAM_SECRET, GL_DEST_REPO)

    def test__should_convert_valid_json_from_repo(self):
        self.client.repo_client.fetch_file_from_repository.return_value = json.dumps(
            dict(foo='bar'))

        result = self.client._load_as_dict_from_repo(
            A_FILE_PATH, A_REPO_NAME, A_BRANCH_NAME, 'json')

        assert result['foo'] == 'bar'

    def test__should_convert_valid_yaml_from_repo(self):
        self.client.repo_client.fetch_file_from_repository.return_value = yaml.dump(
            dict(foo='bar'))

        result_1 = self.client._load_as_dict_from_repo(
            A_FILE_PATH, A_REPO_NAME, A_BRANCH_NAME, 'yaml')
        result_2 = self.client._load_as_dict_from_repo(
            A_FILE_PATH, A_REPO_NAME, A_BRANCH_NAME, 'yml')

        assert result_1['foo'] == 'bar'
        assert result_2['foo'] == 'bar'

    def test__should_raise_exception_if_cannot_convert_config_files_from_repo(self):
        self.client.repo_client.fetch_file_from_repository.return_value = "Robert'); DROP TABLE Stu"

        with self.assertRaises(ConfigException):
            self.client._load_as_dict_from_repo(A_FILE_PATH, A_REPO_NAME, A_BRANCH_NAME, 'sql')

    @patch.object(Client, '_load_as_dict_from_repo', side_effect=['first', 'second'])
    def test__should_load_config_from_repo(self, mock_ladfr):
        result = self.client.load_config(VALID_CONFIG)

        self.client._load_as_dict_from_repo.assert_has_calls([
            call(file_path=ANOTHER_FILE_PATH, filetype=ANOTHER_FILE_TYPE,
                 repo_branch=ANOTHER_BRANCH_NAME, repo_name=ANOTHER_REPO_NAME),
            call(file_path=A_FILE_PATH, filetype=A_FILE_TYPE,
                 repo_branch=A_BRANCH_NAME, repo_name=A_REPO_NAME)
        ])

        assert result == ('first', 'second')

    def test__should_validate_good_specs(self):
        result, msg = self.client.validate_spec(VALID_PROVIDER_SPEC)
        assert (result, msg) == (True, "Validation succeeded.")

        result, msg = self.client.validate_spec(VALID_PROVIDER_SPEC_MULTI_REPOS)
        assert (result, msg) == (True, "Validation succeeded.")

    def test__should_raise_validation_error_on_bad_spec(self):
        result, msg = self.client.validate_spec(INVALID_PROVIDER_SPEC)

        assert not result
        assert msg == "Key 'config' error:\nMissing keys: 'repository', 'scope'"

    def test__basic_preprocessing(self):
        SIMPLE_CONTEXT = {'environment': {'dev': None}}

        targets = self.client.pre_process_spec(VALID_PROVIDER_SPEC_MULTI_REPOS, SIMPLE_CONTEXT)

        assert len(targets) == 2
