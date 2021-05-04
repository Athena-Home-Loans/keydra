import boto3

from datetime import datetime


class CloudwatchClient:
    instance = None

    class __CloudwatchClient:
        def __init__(self, session, region_name=None):
            if session is None:
                session = boto3.session.Session()

            self._client = session.client(
                'cloudwatch', region_name=region_name
            )

        def put_metric_data(self, *args, **kwargs):
            self._client.put_metric_data(*args, **kwargs)

        def put_execution_time(self, name, execution_time):
            self.put_metric_data(
                MetricData=[
                    {
                        'MetricName': 'ExecutionTime',
                        'Dimensions': [
                            {
                                'Name': 'Action',
                                'Value': name
                            }
                        ],
                        'Unit': 'Seconds',
                        'Value': execution_time
                    },
                ],
                Namespace='Keydra'
            )

    def __new__(cls, session, region_name=None):
        if not CloudwatchClient.instance:
            CloudwatchClient.instance = CloudwatchClient.__CloudwatchClient(
                session,
                region_name=region_name
            )

        return CloudwatchClient.instance

    @staticmethod
    def getInstance(session, region_name=None):
        return CloudwatchClient(session, region_name)


def timed(metric_name, specialise=True):
    '''
    Publishes execution time metric to Cloudwatch.

    Metrics are posted under the 'ExecutionTime' metric name, in seconds.

    Attemps to decorate the dimension if `provider` is part of the request.

    :param metric_name: Name of the dimensionality to put metrics against
    :type metric_name: :class:`str`
    :param specialise: Tweak the dimensionality to include the name of the
        provider. If any is found.
    :type specialise: :class:`bool`
    :returns: original return of invoked function or method
    '''
    start = datetime.now()

    def decorator(f):
        def timed_execution(*args, **kwargs):
            dimensionality = metric_name

            # This is pure panic and paranoia! Don't want it to fail rotations
            # or distributions... EVAH!
            try:
                if specialise:
                    for arg in args:
                        if isinstance(arg, dict) and 'provider' in arg:
                            dimensionality = '{}_{}'.format(
                                metric_name,
                                arg.get('provider', 'unknown').lower()
                            )
                            break
            except Exception as e:
                print(
                    'Struggle crafting metric dimensionality: {}'.format(e)
                )

            resp = f(*args, **kwargs)

            try:
                execution_time = (datetime.now() - start).seconds

                CloudwatchClient.getInstance(None).put_execution_time(
                    dimensionality, execution_time
                )
            except Exception as e:
                print(e)

            return resp

        return timed_execution
    return decorator
