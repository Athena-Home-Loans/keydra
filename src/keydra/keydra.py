import copy

from botocore.exceptions import ClientError
from keydra import loader

from keydra import logging as km_logging
from keydra.config import KeydraConfig

from keydra.exceptions import ConfigException, InvalidSecretProvider
from keydra.clients.aws.cloudwatch import CloudwatchClient, timed

LOGGER = km_logging.get_logger()


class Keydra(object):
    def __init__(self, cfg: KeydraConfig, cw: CloudwatchClient, **kwargs):
        self._cfg = cfg
        self._cw = cw

    def rotate_and_distribute(self, run_for_secrets, rotate):
        '''
        AWS Lambda handler

        :param event: Event triggering this function
        :type event: :class:`dict`
        :param context: Lambda Context runtime methods and attributes
        :type context: :class:`object`

        `context` attributes
        ------------------
        '''

        secrets = None

        try:
            secrets = self._cfg.load_secrets(
                secrets=run_for_secrets, rotate=rotate)
        except ConfigException as e:
            LOGGER.error(e)
            return [self._fail(e)]

        if rotate != 'adhoc':
            self._emit_spec_metrics(secrets)

        if not secrets:
            return [self._success(
                'No secrets shortlisted for {} rotation'.format(rotate)
            )]

        LOGGER.debug(
            {
                'message': 'Filtered Secret Specs',
                'data': secrets
            }
        )

        resp = []

        for secret in secrets:
            result = {}
            secret_id = '{}::{}'.format(secret['provider'], secret['key'])

            r_result = self._rotate_secret(secret)

            result['secret_id'] = secret_id
            result['key'] = secret['key']
            result['provider'] = secret['provider']

            result[r_result.pop('action')] = self._redact_secrets(
                r_result, secret)

            if r_result['status'] == 'success' and 'distribute' in secret:
                d_result = self._distribute_secret(secret, r_result['value'])
                result[d_result.pop('action')] = d_result

            resp.append(result)

        if rotate != 'adhoc':
            self._emit_result_metrics(resp)

        return resp

    def _redact_secrets(self, result, spec):
        r_result = copy.deepcopy(result)
        provider = spec['provider']

        LOGGER.debug(
            'Redacting the value of {}::{}'.format(
                spec['provider'],
                spec['key']))

        try:
            km_provider = loader.load_provider_client(provider)

            return km_provider.redact_result(r_result, spec)

        except InvalidSecretProvider:
            pass

        return r_result

    @timed('rotation', specialise=True)
    def _rotate_secret(self, secret):
        action = 'rotate_secret'

        LOGGER.debug({'message': 'Rotating secret', 'data': secret})

        try:
            km = loader.build_client(secret['provider'], secret['key'])

            valid, valid_message = km.validate_spec(secret)

            if not valid:
                return self._fail(valid_message, action=action)

            return self._success(km.rotate(secret), action=action)

        except Exception as e:
            return self._fail(e, action=action)

    @timed('bulk_distribution', specialise=False)
    def _distribute_secret(self, spec, secret):
        action = 'distribute_secret'
        results = []
        has_successes = False
        has_failures = False

        LOGGER.debug({'message': 'Bulk distributing secrets', 'data': spec})

        if 'distribute' not in spec:
            return self._success(
                "No 'distribute' policy in spec. Ignoring.", action=action
            )

        for target in spec['distribute']:
            results.append(self._distribute_single_secret(target, secret))

        for result in results:
            if result.get('status') == 'fail':
                has_failures = True

                if has_successes:
                    break

            elif result.get('status') == 'success':
                has_successes = True

                if has_failures:
                    break

        if has_failures is False:
            return self._success(value=results, action=action)
        else:
            if has_successes:
                return self._partial_success(
                    value=results,
                    msg='Partially successful distribution of secrets',
                    action=action,
                )

        return self._fail(
            msg='Failed to distribute secrets', action=action, value=results
        )

    @timed('distribution', specialise=True)
    def _distribute_single_secret(self, target, secret):
        km_provider = None

        LOGGER.debug(
            {'message': 'Distributing secret to target', 'data': target})

        try:
            km_provider = loader.load_provider_client(target['provider'])
        except InvalidSecretProvider as e:
            return self._fail(e)

        valid, valid_message = km_provider.validate_spec(target)

        if not valid:
            return self._fail(valid_message)

        try:
            km = loader.build_client(
                target['provider'], target.get('provider_secret_key')
            )

            return self._success(km.distribute(secret, target))

        except Exception as e:
            return self._fail(e)

    def _default_response(self, status, action=None, msg=None, value=None):
        response = {
            'status': status,
        }

        if action is not None:
            response['action'] = action

        if msg is not None:
            response['msg'] = msg

        if value is not None:
            response['value'] = value

        return response

    def _fail(self, msg, action=None, value=None):
        return self._default_response('fail',
                                      action=action,
                                      msg=str(msg),
                                      value=value)

    def _success(self, value, action=None):
        return self._default_response('success', action=action, value=value)

    def _partial_success(self, value, msg, action=None):
        return self._default_response(
            'partial_success', action=action, value=value, msg=msg
        )

    # TODO: abstract these metrics functions to a class
    def _emit_spec_metrics(self, secrets):
        total_rotations = len(secrets)
        total_distribution_points = 0

        for secret in secrets:
            total_distribution_points += len(secret.get('distribute', []))

        try:
            self._cw.put_metric_data(
                MetricData=[
                    {
                        'MetricName': 'NumberOfConfiguredRotations',
                        'Dimensions': [
                            {
                                'Name': 'action',
                                'Value': 'rotate_secret'
                            },
                        ],
                        'Unit': 'Count',
                        'Value': total_rotations
                    },
                    {
                        'MetricName': 'NumberOfConfiguredDistributions',
                        'Dimensions': [
                            {
                                'Name': 'action',
                                'Value': 'distribute_secret'
                            },
                        ],
                        'Unit': 'Count',
                        'Value': total_distribution_points
                    },
                ],
                Namespace='Keydra'
            )
        except ClientError as e:
            LOGGER.warn('Not able to emit metrics for config! -> {}'.format(e))

    def _emit_result_metrics(self, results):
        successful_rotations = 0
        failed_rotations = 0
        successful_distributions = 0
        failed_distributions = 0

        for result in results:
            if result['rotate_secret']['status'] == 'success':
                successful_rotations += 1

            elif result['rotate_secret']['status'] == 'fail':
                failed_rotations += 1

            for dresult in \
                    result.get('distribute_secret', {}).get('value', []):
                if dresult['status'] == 'success':
                    successful_distributions += 1

                elif dresult['status'] == 'fail':
                    failed_distributions += 1

        try:
            self._cw.put_metric_data(
                MetricData=[
                    {
                        'MetricName': 'NumberOfSuccessfulRotations',
                        'Dimensions': [
                            {
                                'Name': 'action',
                                'Value': 'rotate_secret'
                            },
                        ],
                        'Unit': 'Count',
                        'Value': successful_rotations
                    },
                    {
                        'MetricName': 'NumberOfFailedRotations',
                        'Dimensions': [
                            {
                                'Name': 'action',
                                'Value': 'rotate_secret'
                            },
                        ],
                        'Unit': 'Count',
                        'Value': failed_rotations
                    },
                    {
                        'MetricName': 'NumberOfSuccessfulDistributions',
                        'Dimensions': [
                            {
                                'Name': 'action',
                                'Value': 'distribute_secret'
                            },
                        ],
                        'Unit': 'Count',
                        'Value': successful_distributions
                    },
                    {
                        'MetricName': 'NumberOfFailedDistributions',
                        'Dimensions': [
                            {
                                'Name': 'action',
                                'Value': 'distribute_secret'
                            },
                        ],
                        'Unit': 'Count',
                        'Value': failed_distributions
                    },
                ],
                Namespace='Keydra'
            )
        except ClientError as e:
            LOGGER.warn('Not able to emit metrics for result! -> {}'.format(e))
