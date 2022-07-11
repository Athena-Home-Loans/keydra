import boto3
import boto3.session

from botocore.exceptions import ClientError


class GetParameterException(Exception):
    pass


class PutParameterException(Exception):
    pass


class SSMClient(object):
    def __init__(self, session=None, region_name=None, **kwargs):
        if not session:
            session = boto3.session.Session()

        self._client = session.client(
            service_name='ssm',
            region_name=region_name
        )

    def parameter_exists(self, param_name) -> bool:
        '''
        Check if an SSM parameter exists

        :param param_name: Name of the parameter
        :type param_name: :class:`str`
        :returns: True if exists, False if not
        :rtype: :class:`bool`
        '''
        resp = self._client.describe_parameters(
            ParameterFilters=[
                {
                    'Key': 'Name',
                    'Values': [param_name],
                }
            ],
            MaxResults=1
        )
        if len(resp['Parameters']) == 1:
            return True

        return False

    def get_parameter_securestring_value(self, param_name) -> str:
        '''
        Retrieves a SecureString parameter from SSM by name

        :param param_name: Name of the parameter
        :type param_name: :class:`str`
        :returns: The decrypted value stored in the parameter
        :rtype: :class:`str`
        '''
        try:
            resp = self._client.get_parameter(
                Name=param_name,
                WithDecryption=True,
            )
            return resp['Parameter']['Value']

        except ClientError as e:
            raise GetParameterException(
                'Error fetching parameter {}: {}'.format(param_name, e)
            )

    def put_parameter_securestring(self, param_name, param_value, description,
                                   tier='Standard', key_id=None) -> dict:
        '''
        Creates or Updates a SecureString parameter in SSM

        :param param_name: Name (identifier) for the parameter
        :type param_name: :class:`str`
        :param param_value: Param value
        :type param_value: :class:`str`
        :param tier: :class:`str`
        :type tier: (Optional) The tier to use ('Standard'|'Advanced'|'Intelligent-Tiering')
        :param key_id: :class:`str`
        :type key_id: (Optional) KMS Id to use for encryption. The default key is used if ommitted.
        :returns: A dictonary with response (bypass from boto)
        :rtype: :class:`dict`

        Sample response:

        {
            'Version': 123,
            'Tier': 'Standard'|'Advanced'|'Intelligent-Tiering'
        }
        '''
        extras = {}
        if key_id:
            extras['KeyId'] = key_id

        if self.parameter_exists(param_name):
            extras['Overwrite'] = True

        else:
            extras['Description'] = description
            extras['Tags'] = [
                {
                    'Key': 'managedby',
                    'Value': 'keydra'
                },
            ]

        try:
            return self._client.put_parameter(
                Name=param_name,
                Value=param_value,
                Type='SecureString',
                Tier=tier,
                **extras
            )
        except ClientError as e:
            raise PutParameterException(
                'Error creating/updating {}: {}'.format(param_name, e)
            )
