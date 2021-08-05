import json
import time

import splunklib.client as splunkclient

import urllib.parse as urlparse

from splunklib.binding import HTTPError

from keydra.logging import get_logger

from keydra.providers.base import exponential_backoff_retry


LOGGER = get_logger()


class AppNotInstalledException(Exception):
    pass


class TaskAlreadyInProgressException(Exception):
    pass


class SplunkClient(object):
    def __init__(self, username, password, host, verify, port=8089):
        '''
        Initializes a Splunk client

        :param username: Username used to connect
        :type username: :class:`string`
        :param password: Password to connect
        :type password: :class:`passwd`
        :param host: The host to connect to
        :type host: :class:`string`
        :param port: The port to use
        :type port: :class:`string`
        :param verify: Verify TLS
        :type verify: :class:`bool`
        '''
        self._service = splunkclient.Service(
            host=host,
            port=port,
            username=username,
            password=password,
            verify=verify
        )
        self._service.login()

    def update_app_config(self, app, path, obj, data):
        '''
        Updates the config of a Splunk app. Will create the
        config entry if it does not already exist.

        :param app: The app context
        :type app: :class:`string`
        :param path: The path to the config object
        :type path: :class:`path`
        :param obj: The config object to update/create
        :type obj: :class:`string`
        :param data: Additional post data
        :type data: :class:`dict`

        :returns: Resulting HTTP status code of the operation
        :rtype: :class:`int`
        '''
        # First check the app is actually installed!
        if self.app_exists(app) is not True:
            raise AppNotInstalledException(
                'App {} not installed on Splunk '
                'host {}'.format(
                    app,
                    self._service.host
                )
            )

        # Try to update the object, throws a HTTPError if fails
        post_data = dict(**data)
        try:
            attempt = self._service.post(
                '/servicesNS/nobody/{app}/'
                '{path}/{object}'.format(
                    app=app,
                    path=path,
                    object=obj
                ),
                **post_data
            )

        except HTTPError as error:
            # We could be here because the object doesn't exist
            # or some other error
            # TODO: Find some way to massage the Splunk API to make this
            #       more robust with status codes than string matching
            if 'does not exist' in str(error.body):
                # Object does not exist, add name and create
                post_data['name'] = obj
                attempt = self._service.post(
                    '/servicesNS/nobody/{app}/'
                    '{path}/{object}'.format(
                        app=app,
                        path=path,
                        object=obj
                    ),
                    **post_data
                )
            else:
                # Something else went wrong
                raise Exception(
                    'Error updating Splunk app {} on '
                    'host {}: {}'.format(
                        app,
                        self._service.host,
                        error
                    )
                )

        return attempt.status

    def update_app_storepass(self, app, username, password, realm=None):
        '''
        Updates a Splunk app storage password. Will create the
        config entry if it does not already exist.

        :param app: The app context
        :type app: :class:`string`
        :param obj: The config object to update/create
        :type obj: :class:`string`
        :param data: Additional post data
        :type data: :class:`dict`

        :returns: Resulting HTTP status code of the operation
        :rtype: :class:`int`
        '''
        if not realm:
            realm = ''

        # First check the app is actually installed!
        if self.app_exists(app) is not True:
            raise AppNotInstalledException(
                'App {} not installed on Splunk '
                'host {}'.format(
                    app,
                    self._service.host
                )
            )

        post_data = {
            'name': username,
            'password': password,
            'realm': realm
        }

        # Craft our URL based on whether the password already exists
        try:
            self._service.get(
                '/servicesNS/nobody/{}/'
                'storage/passwords/{}'.format(app, username)
            )
            url = '/servicesNS/nobody/{}/storage/passwords/{}'.format(
                app,
                username
            )
            post_data.pop('name', None)
            post_data.pop('realm', None)

        except HTTPError:
            url = '/servicesNS/nobody/{}/storage/passwords'.format(app)

        try:
            attempt = self._service.post(url, **post_data)

        except HTTPError as error:
            raise Exception(
                'Error updating Splunk app {} on '
                'host {}: {}'.format(
                    app,
                    self._service.host,
                    error
                )
            )

        return attempt.status

    def app_exists(self, appname):
        '''
        Check if a Splunk app exists

        :param appname: The app name to check for
        :type app: :class:`string`

        :returns: Result of check, True or False
        :rtype: :class:`bool`
        '''
        matching_apps = len(
            self._service.apps.list(search='name={}'.format(appname))
        )
        return matching_apps > 0

    def change_passwd(self, username, oldpasswd, newpasswd):
        '''
        Update a Splunk user account password

        :param username: The username of the account
        :type username: :class:`string`
        :param oldpasswd: The current password of the account
        :type oldpasswd: :class:`passwd`
        :param newpasswd: The new password to change to
        :type newpasswd: :class:`passwd`

        :returns: True if successful
        :rtype: :class:`bool`
        '''
        attempt = self._service.post(
            "/services/authentication/users/{}".format(username),
            password=newpasswd,
            oldpassword=oldpasswd
        )

        if attempt.status != 200:
            raise Exception(
                'Error rotating user {} on Splunk host '
                '{}'.format(username, self._service.host)
            )

        return True

    def rotate_hectoken(self, inputname):
        '''
        Rotate a Splunk HEC token for Splunk Enterprise

        :param inputname: The name of the HTTP input
        :type inputname: :class:`string`

        :returns: New token value if successful
        :rtype: :class:`string`
        '''
        response = self._service.get(
            '/services/data/inputs/http',
            output_mode='json'
        )
        inputs = json.loads(response['body'].read())

        for entry in inputs['entry']:
            if entry['name'] == 'http://'+inputname:
                rotresp = self._service.post(
                    urlparse.unquote(entry['links']['edit']+'/rotate'),
                    output_mode='json'
                )
                newconfig = json.loads(rotresp['body'].read())['entry'][0]

                return newconfig['content']['token']

        raise Exception(
            'Error rotating HEC token {} on Splunk host '
            '{}. Input was not found! Input list: {}'.format(
                inputname,
                self._service.host,
                inputs
            )
        )

    def _get_splunkcloud_httpinput(self, inputname):
        '''
        Get details for a Splunk HEC token on Splunk Cloud (Classic)

        :param inputname: The name of the HTTP input
        :type inputname: :class:`string`

        :returns: Entry details, or an empty list if input not found
        :rtype: :class:`list`
        '''
        getresp = self._service.get(
            '/services/dmc/config/inputs/__indexers/http/{}'.format(inputname),
            output_mode='json'
        )['body'].read()

        return json.loads(getresp)['entry']

    def _get_last_splunkcloud_deploytask(self):
        '''
        Gets the last deployment task to be run on Splunk Cloud (Classic)

        :returns: Last deployment task Id
        :rtype: :class:`string`

        '''
        taskresp = self._service.get(
            '/services/dmc/deploy',
            output_mode='json'
        )['body'].read()
        tasks = json.loads(taskresp)['entry']

        if tasks[0]['name'] == 'lastDeploy':
            return tasks[0]['content']['taskId']
        else:
            raise Exception(
                "Could not fetch last task Id! Task with name 'lastDeploy' was not "
                "found in the Splunk response. Unexpected response from server."
            )

    def _wait_for_splunkcloud_task(self, id, timeout=240):
        '''
        Wait for a Splunk Cloud (Classic) deployment task to complete

        :param id: The task Id to wait for
        :type id: :class:`string`
        :param timeout: How many seconds to wait for before giving up
        :type timeout: :class:`int`

        '''
        attempt = 1
        while attempt < timeout:
            try:
                statusresp = self._service.get(
                    '/services/dmc/tasks/{}'.format(id),
                    output_mode='json'
                )['body'].read()
            except HTTPError:
                raise Exception('Could not fetch status for task {}'.format(id))

            status = json.loads(statusresp)['entry'][0]

            LOGGER.debug("Task {} is currently '{}' after {} seconds.".format(
                    id,
                    status['content']['state'],
                    attempt
                )
            )
            if status['content']['state'] == 'completed':
                LOGGER.info("Deployment task {} completed in {} seconds.".format(id, attempt))
                return

            time.sleep(1)
            attempt += 1

        raise Exception(
            'Deployment task did not complete within {} seconds! Aborting.'.format(timeout)
        )

    @exponential_backoff_retry(5, exception_type=TaskAlreadyInProgressException)
    def _delete_splunkcloud_httpinput(self, inputname):
        '''
        Delete a Splunk HEC token on Splunk Cloud (Classic)

        :param inputname: The name of the HTTP input
        :type inputname: :class:`string`

        :returns: Deployment task Id
        :rtype: :class:`string`

        '''
        # Allow any existing in progress tasks to complete first
        self._wait_for_splunkcloud_task(id=self._get_last_splunkcloud_deploytask())
        try:
            self._service.delete(
                '/services/dmc/config/inputs/__indexers/http/{}'.format(inputname),
                output_mode='json'
            )
        except HTTPError as error:
            if 'deployment task is still in progress' in str(error.body):
                raise TaskAlreadyInProgressException()

            raise Exception(
                'Error deleting input: {}'.format(error)
            )

        return self._get_last_splunkcloud_deploytask()

    @exponential_backoff_retry(5, exception_type=TaskAlreadyInProgressException)
    def _create_splunkcloud_httpinput(self, inputname, inputconfig):
        '''
        Create a Splunk HEC input on Splunk Cloud (Classic)

        :param inputname: The name of the HTTP input
        :type inputname: :class:`string`
        :param inputconfig: The configuration of the new HEC Input
        :type inputconfig: :class:`dict`

        :returns: Tuple of Deployment task Id and deployed configuration
        :rtype: :class:`tuple`

        '''
        self._wait_for_splunkcloud_task(id=self._get_last_splunkcloud_deploytask())
        try:
            createresp = self._service.post(
                '/services/dmc/config/inputs/__indexers/http',
                headers=[('Content-Type', 'application/json')],
                output_mode='json',
                body=json.dumps(inputconfig)
            )

        except HTTPError as error:
            if 'deployment task is still in progress' in str(error.body):
                LOGGER.info('Could not deploy task, another task is already in progress. Retrying.')
                raise TaskAlreadyInProgressException()

            raise Exception(
                'Error creating input: {}'.format(error)
            )

        response = json.loads(createresp['body'].read())

        return self._get_last_splunkcloud_deploytask(), response['entry'][0]

    def rotate_hectoken_cloud(self, inputname):
        '''
        Rotate a Splunk HEC token on Splunk Cloud (Classic)

        Unfortunately you can rotate in place on Splunk Cloud, so we have
        to delete and recreate the HTTP input in order to get a new token.

        https://docs.splunk.com/Documentation/SplunkCloud/8.2.2105/Admin/ManageHECtokens

        :param inputname: The name of the HTTP input
        :type inputname: :class:`string`

        :returns: New token value if successful
        :rtype: :class:`string`

        '''
        LOGGER.debug('Getting input details for {}'.format(inputname))

        inputs = self._get_splunkcloud_httpinput(inputname)

        if len(inputs) == 0:
            raise Exception('Input {} was not found!'.format(inputname))
        else:
            httpinput = inputs[0]

        LOGGER.debug('Found input.')

        config = {
            'name': httpinput['name'],
        }
        content = httpinput['content']
        content.pop('token', None)
        content.pop('host', None)

        config.update(content)

        LOGGER.debug('Using config {}'.format(config))

        taskId = self._delete_splunkcloud_httpinput(inputname)
        LOGGER.info('Input {} delete in progress under task Id {}'.format(inputname, taskId))

        self._wait_for_splunkcloud_task(id=taskId)
        LOGGER.debug('Deleted input successfully')

        createTaskId, newconfig = self._create_splunkcloud_httpinput(
            inputname=inputname,
            inputconfig=config
        )
        LOGGER.info('Input {} create in progress under task Id {}'.format(inputname, taskId))

        return newconfig['content']['token']
