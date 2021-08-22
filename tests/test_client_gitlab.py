import unittest
from collections import namedtuple
from unittest.mock import MagicMock, patch

from keydra.clients.gitlab import GitlabClient

RepoVar = namedtuple('RepoVar', ['key', 'value'])

A_BRANCH_NAME = "feature/branch"
A_FILE_PATH = "path/to/a.file"
A_REPO_NAME = "my-group/my-repo"
A_REPO_VAR = RepoVar('foo', '0')
ANOTHER_REPO_VAR = RepoVar('bar', '1')


class TestGitlabClient(unittest.TestCase):

    def setUp(self):
        self.glc = GitlabClient.__new__(GitlabClient)
        self.glc.gpc = MagicMock()
        self.glc.PROJECT_CACHE = {}

    def test__should_set_cache_when_creating_projectmanager(self):
        project_manager = MagicMock()
        project_manager.get.return_value = 'the project manager'
        self.glc.gpc.projects = project_manager

        result = self.glc._get_project_manager(A_REPO_NAME)

        assert result == 'the project manager'
        assert self.glc.PROJECT_CACHE == {'my-group/my-repo': 'the project manager'}

    def test__should_use_cache_when_retrieving_projectmanager(self):
        self.glc.gpc.projects = MagicMock()
        self.glc.PROJECT_CACHE = {'my-group/my-repo': 'the project manager'}

        result = self.glc._get_project_manager(A_REPO_NAME)

        assert result == 'the project manager'
        self.glc.gpc.projects.get.assert_not_called()

    @patch.object(GitlabClient, '_get_project_manager')
    def test__should_consider_new_variable_as_new(self, mock_gpm):
        mock_vm = MagicMock()
        mock_vm.variables.list.return_value = [A_REPO_VAR]
        mock_gpm.return_value = mock_vm

        assert self.glc._is_new_repo_variable(A_REPO_NAME, ANOTHER_REPO_VAR.key) is True

    @patch.object(GitlabClient, '_get_project_manager')
    def test__should_not_consider_existing_variable_as_new(self, mock_gpm):
        mock_vm = MagicMock()
        mock_vm.variables.list.return_value = [A_REPO_VAR]
        mock_gpm.return_value = mock_vm

        assert self.glc._is_new_repo_variable(A_REPO_NAME, A_REPO_VAR.key) is False

    @patch.object(GitlabClient, '_is_new_repo_variable', return_value=True)
    @patch.object(GitlabClient, '_get_project_manager')
    def test__should_create_repo_variable_if_new(self, mock_gpm, mock_inrp):
        mock_vm = MagicMock()
        mock_gpm.return_value = mock_vm

        self.glc.set_repo_variable(A_REPO_NAME, A_REPO_VAR.key, A_REPO_VAR.value)

        mock_vm.variables.create.assert_called_once_with(
            {'key': A_REPO_VAR.key, 'value': A_REPO_VAR.value})

    @patch.object(GitlabClient, '_is_new_repo_variable', return_value=False)
    @patch.object(GitlabClient, '_get_project_manager')
    def test__should_update_repo_variable_if_already_existing(self, mock_gpm, mock_inrp):
        mock_vm = MagicMock()
        mock_gpm.return_value = mock_vm

        self.glc.set_repo_variable(A_REPO_NAME, A_REPO_VAR.key, A_REPO_VAR.value)

        mock_vm.variables.get.assert_called_once_with(A_REPO_VAR.key)

    @patch.object(GitlabClient, '_get_project_manager')
    def test__should_fetch_file_from_repo(self, mock_gpm):
        mock_fm = MagicMock()
        mock_fm.variables.list.return_value = [A_REPO_VAR]
        mock_gpm.return_value = mock_fm

        self.glc.fetch_file_from_repository(A_FILE_PATH, A_REPO_NAME, A_BRANCH_NAME)

        mock_fm.files.get.assert_called_once_with(file_path=A_FILE_PATH, ref=A_BRANCH_NAME)

    @patch.object(GitlabClient, '_get_project_manager')
    def test__should_fetch_file_from_repo_with_default_branch_name_if_not_provided(self, mock_gpm):
        mock_fm = MagicMock()
        mock_fm.variables.list.return_value = [A_REPO_VAR]
        mock_gpm.return_value = mock_fm

        self.glc.fetch_file_from_repository(A_FILE_PATH, A_REPO_NAME)

        mock_fm.files.get.assert_called_once_with(file_path=A_FILE_PATH, ref='main')
