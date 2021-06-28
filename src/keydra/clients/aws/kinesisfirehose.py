import boto3
import boto3.session

from botocore.exceptions import ClientError


class UpdateSecretException(Exception):
    pass


class FirehoseClient(object):
    def __init__(self, session=None, region_name=None, **kwargs):
        if not session:
            session = boto3.session.Session()

        self._client = session.client(
            service_name='firehose',
            region_name=region_name
        )

    def stream_exists(self, streamname):
        '''
        Check it a stream exists

        :param streamname: Name of the Firehose Delivery Stream
        :type secret_name: :class:`str`
        :returns: True if stream exists, else False
        :rtype: :class:`bool`
        '''
        try:
            self._client.describe_delivery_stream(
                DeliveryStreamName=streamname
            )
            return True
        except Exception:
            return False

    def _get_stream_ids(self, streamname, desttype):
        '''
        Get the version Id of a stream, and the dest Id of its destination

        :param streamname: Name of the Firehose Delivery Stream
        :type streamname: :class:`str`
        :param desttype: The destination type - 'Splunk' or 'HTTPEndpoint'
        :type desttype: :class:`str`
        :returns: A tuple with version and dest Id, or None if stream/dest not found
        :rtype: :class:`tuple`
        '''
        if desttype not in ['Splunk', 'HttpEndpoint']:
            raise Exception("Unknown destination type - must be 'Splunk' or 'HttpEndpoint'")

        stream_details = self._client.describe_delivery_stream(
            DeliveryStreamName=streamname
        )['DeliveryStreamDescription']

        versionid = stream_details['VersionId']

        destid = None
        for dest in stream_details['Destinations']:
            if '{}DestinationDescription'.format(desttype) in dest:
                destid = dest['DestinationId']
                break

        return versionid, destid

    def _get_HttpEndpointConfiguration(self, streamname, destId):
        dests = self._client.describe_delivery_stream(
            DeliveryStreamName=streamname
        )['DeliveryStreamDescription']['Destinations']

        for dest in dests:
            if dest['DestinationId'] == destId:
                return dest['HttpEndpointDestinationDescription']['EndpointConfiguration']

        raise Exception(
            'Could not find endpoint config for stream {} with dest Id {}'.format(
                streamname, destId
            )
        )

    def update_splunk_hectoken(self, streamname, token):
        '''
        Updates the HEC Token of a Firehose Splunk destination

        :param streamname: Name of the Firehose Delivery Stream
        :type streamname: :class:`str`
        :param token: Secret value
        :type token: :class:`str`
        :returns: A dictonary with response (bypass from boto)
        :rtype: :class:`dict`

        '''
        try:
            versionid, destid = self._get_stream_ids(streamname=streamname, desttype='Splunk')

            if not destid:
                raise UpdateSecretException(
                    "Stream '{}' does not have a Splunk Destination to update!".format(
                        streamname
                    )
                )

            return self._client.update_destination(
                DeliveryStreamName=streamname,
                CurrentDeliveryStreamVersionId=versionid,
                DestinationId=destid,
                SplunkDestinationUpdate={'HECToken': token}
            )

        except ClientError as e:
            raise UpdateSecretException(
                'Error updating Splunk Destination {}: {}'.format(streamname, e)
            )

    def update_http_accesskey(self, streamname, key):
        '''
        Updates the access key of a Firehose HTTP destination

        :param streamname: Name of the Firehose Delivery Stream
        :type secret_name: :class:`str`
        :param token: Secret value
        :type token: :class:`str`
        :returns: A dictonary with response (bypass from boto)
        :rtype: :class:`dict`

        '''
        try:
            versionid, destid = self._get_stream_ids(
                streamname=streamname,
                desttype='HttpEndpoint'
            )

            if not destid:
                raise UpdateSecretException(
                    "Stream '{}' does not have a HTTP Endpoint Destination to update!".format(
                        streamname
                    )
                )

            EndpointConfiguration = self._get_HttpEndpointConfiguration(streamname, destid)
            EndpointConfiguration['AccessKey'] = key

            return self._client.update_destination(
                DeliveryStreamName=streamname,
                CurrentDeliveryStreamVersionId=versionid,
                DestinationId=destid,
                HttpEndpointDestinationUpdate={
                    'EndpointConfiguration': EndpointConfiguration
                }
            )

        except ClientError as e:
            raise UpdateSecretException(
                'Error updating HTTP Destination {}: {}'.format(streamname, e)
            )
