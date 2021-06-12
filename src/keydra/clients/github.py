import requests
import json

from copy import deepcopy

from base64 import b64encode

from nacl import encoding, public


API_URL = 'https://api.github.com'


class GithubClient(object):
    def __init__(self, user, passwd):
        '''
        Initializes a client for Github

        :param user: Github username
        :type user: :class:`str`
        :param passwd: Github personal access token
        :type passwd: :class:`passwd`
        '''
        self._authorizer = {
            'Content-Type': 'application/json',
            'Authorization': 'token {}'.format(passwd)
        }

    def _query(self, url, extraheaders=None):

        if extraheaders:
            headers = deepcopy(self._authorizer)
            headers.update(extraheaders)
        else:
            headers = self._authorizer

        resp = requests.get(url, headers=headers)

        resp.raise_for_status()

        return resp.text

    def _post(self, url, **kwargs):
        resp = requests.post(url, auth=self._authorizer, **kwargs)

        resp.raise_for_status()

        return resp.text

    def _put(self, url, **kwargs):
        resp = requests.put(url, headers=self._authorizer, **kwargs)

        resp.raise_for_status()

        return resp.text

    def _delete(self, url):
        resp = requests.delete(url, auth=self._authorizer)

        resp.raise_for_status()

        return resp.text

    def _get_repo_public_key(self, org, repo):
        url = '{}/repos/{}/{}/actions/secrets/public-key'.format(
            API_URL, org, repo
        )

        return json.loads(self._query(url))

    def _encrypt_secret(self, secret, public_key):
        '''
        Encrypt a secret string using the orgs public key
        https://docs.github.com/en/rest/reference/actions#create-or-update-an-organization-secret

        :param secret: Slug of the repository to be queried
        :type repo_slug: :class:`str`
        :returns: Encypted secret
        :rtype: :class:`str`
        '''
        public_key = public.PublicKey(public_key['key'].encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret.encode("utf-8"))

        return b64encode(encrypted).decode("utf-8")

    def list_repo_variables(
        self,
        repo,
        org
    ):
        '''
        Lists all the variables configured for a given repository
        https://docs.github.com/en/rest/reference/actions#list-repository-secrets

        :param repo: Repository to be queried
        :type repo: :class:`str`
        :param org: Organisation the repo belongs to
        :type org: :class:`str`
        :returns: A list of dicts describing secrets
        :rtype: :class:`list` of :class:`dict`
        '''

        url = '{}/repos/{}/{}/actions/secrets'.format(
            API_URL, org, repo
        )

        return self._query(url)['secrets']

    def add_repo_variable(
        self,
        repo,
        key,
        value,
        org
    ):
        '''
        Add a new variable for a specific repository
        https://docs.github.com/en/rest/reference/actions#create-or-update-an-environment-secret

        :param repo: Slug of the repository to be queried
        :type repo: :class:`str`
        :param key: Key for the variable in the repo
        :type key: :class:`str`
        :param value: Value for the variable in the repo
        :type value: :class:`str`
        :param org: Organisation the repo is in
        :type org: :class:`str`
        :returns: A description of the variable added
        :rtype: :class:`dict`
        '''
        url = '{}/repos/{}/{}/actions/secrets/{}'.format(
            API_URL, org, repo, key
        )

        pubkey = self._get_repo_public_key(org=org, repo=repo)

        encrypted = self._encrypt_secret(
            public_key=pubkey,
            secret=value
        )

        payload = {
            'key_id': pubkey['key_id'],
            'encrypted_value': encrypted
        }

        return self._put(url, json=payload)

    def fetch_file_from_repository(
        self,
        org,
        repo,
        path
    ):
        '''
        Reads file from Github
        https://docs.github.com/rest/reference/repos#get-repository-content

        :param org: GH account name
        :type org: :class:`str`
        :param repo: Name of the repository to fetch file from
        :type repo: :class:`str`
        :param path: Path to the file in the repo
        :type repo: :class:`str`
        :returns: Content of the file
        :rtype: :class:`str`
        '''

        extras = {
            'Accept': 'application/vnd.github.v4.raw'
        }
        url = '{}/repos/{}/{}/contents/{}'.format(API_URL, org, repo, path)

        return self._query(url, extraheaders=extras)
