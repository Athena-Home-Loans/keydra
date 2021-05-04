import requests

from requests.auth import HTTPBasicAuth


API_URL = 'https://api.bitbucket.org/2.0'
API_TEAM = '{}/teams'.format(API_URL)
API_REPO = '{}/repositories'.format(API_URL)


class BitbucketClient(object):
    def __init__(self, user, passwd):
        '''
        Initializes a client for Bitbucket

        :param user: Bitbucket username
        :type user: :class:`str`
        :param passwd: Bitbucket password
        :type passwd: :class:`passwd`
        '''
        self._authorizer = HTTPBasicAuth(user, passwd)

    def _query(self, url):
        resp = requests.get(url, auth=self._authorizer)

        resp.raise_for_status()

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _post(self, url, **kwargs):
        resp = requests.post(url, auth=self._authorizer, **kwargs)

        resp.raise_for_status()

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _put(self, url, **kwargs):
        resp = requests.put(url, auth=self._authorizer, **kwargs)

        resp.raise_for_status()

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _delete(self, url):
        resp = requests.delete(url, auth=self._authorizer)

        resp.raise_for_status()

        return {'status': resp.status_code, 'text': resp.text}

    def _fetch_all(self, query):
        entries = []
        page = 1
        url = '{}?page={}'.format(query, page)

        while True:
            resp = self._query(url)

            if resp['pagelen'] < 1:
                break

            for entry in resp.get('values', []):
                entries.append(entry)

            page += 1
            url = '{}?page={}'.format(query, page)

            if len(entries) >= resp['size']:
                break

        return entries

    def list_team_pipeline_variables(self, username):
        '''
        Lists all "account level" variables in Bitbucket

        Note: this will list every single page of variables existing in the
            account

        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A list of dictionaries describing variables (as per BB API)
        :rtype: :class:`list` of :class:`dict`
        '''
        url = '{}/{}/pipelines_config/variables/'.format(API_TEAM, username)

        return self._fetch_all(url)

    def add_team_pipeline_variable(
        self,
        key,
        value,
        username,
        secured=True,
    ):
        '''
        Adds an "account level" variable in Bitbucket

        :param key: Variable key (how it is going to be accessed)
        :type key: :class:`str`
        :param value: Value of the variable
        :type value: :class:`str`
        :param secured: Should this variable be hidden from humans?
        :type secured: :class:`bool`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: Description of the newly added variable (as per BB API)
        :rtype: :class:`dict`
        '''
        url = '{}/{}/pipelines_config/variables/'.format(API_TEAM, username)

        payload = {
            'type': 'pipeline_variable',
            'key': key,
            'value': value,
            'secured': secured,
        }

        return self._post(url, json=payload)

    def update_team_pipeline_variable(
        self,
        uuid,
        key,
        value,
        username,
        secured=True,
    ):
        '''
        Updates an "account level" variable in Bitbucket

        :param uuid: UUID of the variable in Bitbucket
        :type uuid: :class:`str`
        :param key: Variable key (how it is going to be accessed)
        :type key: :class:`str`
        :param value: Value of the variable
        :type value: :class:`str`
        :param secured: Should this variable be hidden from humans?
        :type secured: :class:`bool`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: Description of the updated variable (as per BB API)
        :rtype: :class:`dict`
        '''
        url = '{}/{}/pipelines_config/variables/{}'.format(
            API_TEAM,
            username,
            uuid
        )

        payload = {
            'type': 'pipeline_variable',
            'key': key,
            'value': value,
            'secured': secured,
        }

        return self._put(url, json=payload)

    def delete_team_pipeline_variable(self, uuid, username):
        '''
        Deletes an "account level" variable in Bitbucket

        :param uuid: UUID of the variable in Bitbucket
        :type uuid: :class:`str`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: JSON response
        :rtype: :class:`dict`
        '''
        url = '{}/{}/pipelines_config/variables/{}'.format(
            API_TEAM,
            username,
            uuid
        )

        return self._delete(url)

    def list_repo_environments(self, repo_slug, username):
        '''
        Lists all the environments configured for the given repository

        :param repo_slug: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A list of dictionaries describing environments
            (as per BB API)
        :rtype: :class:`list` of :class:`dict`
        '''
        url = '{}/{}/{}/environments/'.format(API_REPO, username, repo_slug)

        return self._fetch_all(url)

    def add_repo_environment(
        self,
        repo_slug,
        name,
        username,
        env_type='Production',
        admin_locked=False,
    ):
        '''
        Add new environments to the given repository

        :param repo_slug: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :param name: Name of the environment to be added
        :type name: :class:`str`
        :param env_type: Type of the environment (Test/Staging/Production)
        :type env_type: :class:`str`
        :param admin_locked: Should this env be locked to admins only?
        :type admin_locked: :class:`bool`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A description of the added environment (as per BB API)
        :rtype: :class:`dict`
        '''
        url = '{}/{}/{}/environments/'.format(API_REPO, username, repo_slug)

        payload = {
            'type': 'deployment_environment',
            'environment_type': {
                'type': 'deployment_environment_type',
                'name': env_type
            },
            'name': name,
        }

        if env_type.lower() == 'production' or admin_locked:
            payload['environment_lock_enabled'] = True
            payload['restrictions'] = {
                'type': 'deployment_restrictoins_configuration',
                'admin_only': True
            }

        return self._post(url, json=payload)

    def list_repo_deployment_variables(
        self,
        repo_slug,
        env_uuid,
        username
    ):
        '''
        Lists all the deployment variables configured for a specific
        environments in the given repository

        :param repo_slug: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :param env_uuid: UUID of the environment to be updated
        :type env_uuid: :class:`str`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A list of dictionaries describing environments
            (as per BB API)
        :rtype: :class:`list` of :class:`dict`
        '''
        url = '{}/{}/{}/deployments_config/environments/{}/variables'.format(
            API_REPO, username, repo_slug, env_uuid
        )

        return self._fetch_all(url)

    def add_repo_deployment_variable(
        self,
        repo_slug,
        env_uuid,
        key,
        value,
        username,
        secured=True,
    ):
        '''
        Add a new deployment variables configured for a specific environments
        in the given repository

        :param repo_slug: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :param env_uuid: UUID of the environment to be updated
        :type env_uuid: :class:`str`
        :param key: Key for the variable in the deployment environment
        :type key: :class:`str`
        :param value: Value for the variable in the deployment environment
        :type value: :class:`str`
        :param secured: Should this variable be hidden from humans?
        :type secured: :class:`bool`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A description of the variable added (as per BB API)
        :rtype: :class:`dict`
        '''
        url = '{}/{}/{}/deployments_config/environments/{}/variables'.format(
            API_REPO, username, repo_slug, env_uuid
        )

        payload = {
            'type': 'pipeline_variable',
            'key': key,
            'value': value,
            'secured': secured,
        }

        return self._post(url, json=payload)

    def update_repo_deployment_variable(
        self,
        repo_slug,
        env_uuid,
        var_uuid,
        key,
        value,
        username,
        secured=True,
    ):
        '''
        Updates an existing deployment variables configured for a specific
        environments in the given repository

        :param repo_slug: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :param env_uuid: UUID of the environment to be updated
        :type env_uuid: :class:`str`
        :param var_uuid: UUID of the variable in Bitbucket
        :type var_uuid: :class:`str`
        :param key: Key for the variable in the deployment environment
        :type key: :class:`str`
        :param value: Value for the variable in the deployment environment
        :type value: :class:`str`
        :param secured: Should this variable be hidden from humans?
        :type secured: :class:`bool`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A description of the variable added (as per BB API)
        :rtype: :class:`dict`
        '''
        url = '{}/{}/{}/deployments_config/environments/{}/variables/{}'.format(  # noqa
            API_REPO, username, repo_slug, env_uuid, var_uuid
        )

        payload = {
            'type': 'pipeline_variable',
            'key': key,
            'value': value,
            'secured': secured,
        }

        return self._put(url, json=payload)

    def list_repo_variables(
        self,
        repo_slug,
        username
    ):
        '''
        Lists all the variables configured for a given repository

        :param repo_slug: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A list of dictionaries describing environments
            (as per BB API)
        :rtype: :class:`list` of :class:`dict`
        '''
        url = '{}/{}/{}/pipelines_config/variables/'.format(
            API_REPO, username, repo_slug
        )

        return self._fetch_all(url)

    def add_repo_variable(
        self,
        repo_slug,
        key,
        value,
        username,
        secured=True,
    ):
        '''
        Add a new variable for a specific repository

        :param repo_slug: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :param key: Key for the variable in the deployment environment
        :type key: :class:`str`
        :param value: Value for the variable in the deployment environment
        :type value: :class:`str`
        :param secured: Should this variable be hidden from humans?
        :type secured: :class:`bool`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A description of the variable added (as per BB API)
        :rtype: :class:`dict`
        '''
        url = '{}/{}/{}/pipelines_config/variables/'.format(
            API_REPO, username, repo_slug
        )

        payload = {
            'type': 'pipeline_variable',
            'key': key,
            'value': value,
            'secured': secured,
        }

        return self._post(url, json=payload)

    def update_repo_variable(
        self,
        repo_slug,
        var_uuid,
        key,
        value,
        username,
        secured=True,
    ):
        '''
        Updates an existing deployment variables configured for a specific
        environments in the given repository

        :param repo_slug: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :param env_uuid: UUID of the environment to be updated
        :type var_uuid: :class:`str`
        :param key: Key for the variable in the deployment environment
        :type key: :class:`str`
        :param value: Value for the variable in the deployment environment
        :type value: :class:`str`
        :param secured: Should this variable be hidden from humans?
        :type secured: :class:`bool`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: A description of the variable added (as per BB API)
        :rtype: :class:`dict`
        '''
        url = '{}/{}/{}/pipelines_config/variables/{}'.format(
            API_REPO, username, repo_slug, var_uuid
        )

        payload = {
            'type': 'pipeline_variable',
            'key': key,
            'value': value,
            'secured': secured,
        }

        return self._put(url, json=payload)

    def fetch_file_from_repository(
        self,
        repo,
        path,
        username
    ):
        '''
        Reads file from Bitbucket

        *Notes*: Requires 'repository' privilege

        :param repo: Name of the repository to fetch file from
        :type repo: :class:`str`
        :param path: Path to the file on repo
        :type repo: :class:`str`
        :param username: Username of the team account
        :type username: :class:`str`
        :returns: Content of the file
        :rtype: :class:`str`
        '''
        url = '{}/{}/{}/{}'.format(API_REPO, username, repo, path)

        return self._query(url)
