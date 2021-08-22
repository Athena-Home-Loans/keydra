from gitlab import Gitlab as GitlabPythonClient
from gitlab.v4.objects import ProjectManager

from keydra.logging import get_logger

LOGGER = get_logger()
API_URL = 'https://gitlab.com/'


class GitlabClient:

    def __init__(self, access_token) -> None:
        '''
        Initializes a client for Gitlab

        :param access_token: Project Access Token
        :type access_token: :class:`str`
        '''
        self.gpc = GitlabPythonClient(API_URL, access_token)
        self.PROJECT_CACHE = {}

    def _get_project_manager(self, repo_name) -> ProjectManager:
        if not self.PROJECT_CACHE.get(repo_name):
            self.PROJECT_CACHE[repo_name] = self.gpc.projects.get(repo_name)
        return self.PROJECT_CACHE[repo_name]

    def _is_new_repo_variable(self, repo_name, key) -> bool:
        pm = self._get_project_manager(repo_name)
        return key not in [project_var.key for project_var in pm.variables.list()]

    def set_repo_variable(self, repo_name, key, value) -> None:
        '''
        Sets a variable for a specific repository. Creates new variable or updates existing.

        :param repo_name: Full repository name, including group(s) (my-group/my-repo)
        :type repo: :class:`str`
        :param key: Key for the variable in the repo
        :type key: :class:`str`
        :param value: Value for the variable in the repo
        :type value: :class:`str`
        '''
        pm = self._get_project_manager(repo_name)
        if self._is_new_repo_variable(repo_name, key):
            LOGGER.info('Creating project variable {}...'.format(key))
            pm.variables.create(dict(key=key, value=value, ))
        else:
            LOGGER.info('Updating project variable {}...'.format(key))
            project_var = pm.variables.get(key)
            project_var.value = value
            project_var.save()

    def fetch_file_from_repository(self, file_path, repo_name, repo_branch='main') -> str:
        '''
        Reads file from repository.

        :param file_path: Path in repo, e.g. foo/bar/baz.yaml
        :type file_path: :class:`str`
        :param repo_name: Full repository name, including group(s) (my-group/my-repo)
        :type repo_name: :class:`str`
        :param repo_branch: Branch to read file from (optional)
        :type repo_branch: :class:`str`
        :returns: Content of the file
        :rtype: :class:`str`
        '''
        pm = self._get_project_manager(repo_name)
        encoded_file = pm.files.get(
            file_path=file_path,
            ref=repo_branch
        )
        return encoded_file.decode()
