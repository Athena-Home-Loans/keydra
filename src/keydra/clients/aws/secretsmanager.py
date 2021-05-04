import boto3
import boto3.session

from botocore.exceptions import ClientError


class GetSecretException(Exception):
    pass


class UpdateSecretException(Exception):
    pass


class InsertSecretException(Exception):
    pass


class SecretsManagerClient(object):
    def __init__(self, session=None, region_name=None, **kwargs):
        if not session:
            session = boto3.session.Session()

        self._client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

    def get_secret_value(self, secret_id, version_stage='current') -> str:
        '''
        Retrieves a secret from SecretsManager by name and stage

        :param secret_id: ID (ARN or friendly secret name) of the secret
        :type secret_id: :class:`str`
        :param version_stage: Version stage of the secret (current/previous)
        :type version_stage: :class:`str`
        :returns: The secret matching the request
        :rtype: :class:`str`
        '''
        stage = version_stage

        if version_stage.lower() == 'previous':
            stage = 'AWSPREVIOUS'
        elif version_stage.lower() == 'current':
            stage = 'AWSCURRENT'

        resp = self._client.get_secret_value(
            SecretId=secret_id,
            VersionStage=stage
        )

        return resp['SecretString']

    def create_secret(self, secret_name, secret_value, **kwargs):
        '''
        Creates secret in SecretsManager

        :param secret_name: Name (identifier) for the secret
        :type secret_name: :class:`str`
        :param secret_value: Secret value
        :type secret_value: :class:`str`
        :param description: (Optional) Description of the secret
        :type description: :class:`str`
        :returns: A dictonary with response (bypass from boto)
        :rtype: :class:`dict`

        Sample response:

        {
            'ARN': :class:`str`,
            'Name': :class:`str`,
            'VersionId': :class:`str`
        }
        '''
        try:
            return self._client.create_secret(
                Name=secret_name,
                Description=kwargs.get('description', ''),
                SecretString=secret_value,
                Tags=[
                    {
                        'Key': 'managedby',
                        'Value': 'keydra'
                    },
                ]
            )
        except ClientError as e:
            raise InsertSecretException(
                'Error inserting {}: {}'.format(secret_name, e)
            )

    def describe_secret(self, secret_id):
        '''
        Retrieves the details of a secret. It does not include the encrypted
        fields. Only those fields that are populated with a value are returned
        in the response.

        :param secret_id: ID (ARN or friendly secret name) of the secret
        :type secret_id: :class:`str`
        :returns: Description of the secret (minus encrypted bits)
        :rtype: :class:`dict`
        :raises: :class:`GetSecretException` if secret doesn't exist

        Sample response:

        {
            'ARN': :class:`str`,
            'Name': :class:`str`,
            'Description': :class:`str`,
            'KmsKeyId': :class:`str`,
            'RotationEnabled': :class:`bool`,
            'RotationLambdaARN': :class:`str`,
            'RotationRules': {
                'AutomaticallyAfterDays': :class:`int`
            },
            'LastRotatedDate': :class:`datetime`,
            'LastChangedDate': :class:`datetime`,
            'LastAccessedDate': :class:`datetime`,
            'DeletedDate': :class:`datetime`,
            'Tags': [
                {
                    'Key': :class:`str`,
                    'Value': :class:`str`
                },
            ],
            'VersionIdsToStages': {
                :class:`str`: [
                    :class:`str`,
                ]
            },
            'OwningService': :class:`str`
        }
        '''
        try:
            return self._client.describe_secret(
                SecretId=secret_id
            )
        except ClientError as e:
            raise GetSecretException(
                'Error accessing {}: {}'.format(secret_id, e)
            )

    def update_secret(self, secret_id, secret_value):
        '''
        Stores a new encrypted secret value in the specified secret by
        creating a new version and attaching it to the secret with the label
        AWSCURRENT (which will trigger the rotation of the label in any
        existing secrets to AWSPREVIOUS)

        :param secret_id: ID (ARN or friendly secret name) of the secret
        :type secret_id: :class:`str`
        :param secret_value: Secret value
        :type secret_value: :class:`str`
        :returns: Details about the secret updated
        :rtype: :class:`dict`
        :raises: :class:`GetSecretException` if secret doesn't exist

        Sample response:

        {
            'ARN': :class:`str`,
            'Name': :class:`str`,
            'VersionId': :class:`str`,
            'VersionStages': [
                :class:`str`,
            ]
        }
        '''
        try:
            return self._client.put_secret_value(
                SecretId=secret_id,
                SecretString=secret_value,
                VersionStages=[
                    'AWSCURRENT',
                ]
            )
        except ClientError as e:
            raise UpdateSecretException(
                'Error updating {}: {}'.format(secret_id, e)
            )

    def update_secret_description(self, secret_id, description):
        '''
        Updates the description of a secret

        :param secret_id: ID (ARN or friendly secret name) of the secret
        :type secret_id: :class:`str`
        :param description: Description of the Secret
        :type description: :class:`dict`
        :returns: Details about the secret updated
        :rtype: :class:`dict`

        Sample response:

        {
            'ARN': :class:`str`,
            'Name': :class:`str`,
            'VersionId': :class:`str`
        }
        '''
        try:
            return self._client.update_secret(
                SecretId=secret_id,
                Description=description
            )
        except ClientError as e:
            raise UpdateSecretException(
                'Error updating {}: {}'.format(secret_id, e)
            )

    def generate_random_password(self, length=32, **kwargs):
        '''
        Generates a random password of the specified complexity.

        :param length: Length of the password
        :type length: :class:`int`
        :returns: A randomly generated password compliant with the spec
            provided
        :rtype: :class:`str`

        Optional parameters:

        ExcludeCharacters=:class:`str`
        ExcludeNumbers=:class:`bool`
        ExcludePunctuation=:class:`bool`
        ExcludeUppercase=:class:`bool`
        ExcludeLowercase=:class:`bool`
        IncludeSpace=:class:`bool`
        RequireEachIncludedType=:class:`bool`
        '''
        kwargs['PasswordLength'] = length

        return self._client.get_random_password(**kwargs)['RandomPassword']
