from botocore.exceptions import ClientError

from keydra import loader
from keydra import logging as km_logging
from keydra.clients.aws.cloudwatch import CloudwatchClient, timed
from keydra.config import KeydraConfig
from keydra.exceptions import ConfigException, InvalidSecretProvider

LOGGER = km_logging.get_logger()


class Keydra(object):
    def __init__(self, cfg: KeydraConfig, cw: CloudwatchClient):
        self._cfg = cfg
        self._cw = cw

    def rotate_and_distribute(self, run_for_secrets, rotate, batch_number=None, number_of_batches=None) -> list[dict]:
        try:
            secrets = self._cfg.load_secrets(
                secrets=run_for_secrets,
                rotate=rotate,
                batch_number=batch_number,
                number_of_batches=number_of_batches
            )
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

        response: list[dict] = []

        for secret in secrets:
            result = {}
            secret_id = '{}::{}'.format(secret['provider'], secret['key'])

            r_result = self._rotate_secret(secret)

            result['secret_id'] = secret_id
            result['key'] = secret['key']
            result['provider'] = secret['provider']

            result[r_result.pop('action')] = self._redact_secrets(r_result, secret)

            if r_result['status'] == 'success' and 'distribute' in secret:
                d_result = self._distribute_secret(secret, r_result['value'])
                result[d_result.pop('action')] = d_result

            response.append(result)

        if rotate != 'adhoc':
            self._emit_result_metrics(response)

        return response

    @staticmethod
    def _redact_secrets(result: dict, spec: dict):
        LOGGER.debug('Redacting the value of {}::{}'.format(spec['provider'], spec['key']))
        km_provider = loader.load_provider_client(spec['provider'])
        return km_provider.redact_result(result, spec)

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
            LOGGER.error(
                "Failed to rotate key '{}' for provider '{}'!".format(
                    secret['key'],
                    secret['provider']
                )
            )
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
            if callable(getattr(km, "load_config")):
                LOGGER.debug(
                    "{} is a config provider! Setting default org/account.".format(
                        target['provider']
                    )
                )
                km.accountusername = self._cfg.get_account_username()

            return self._success(km.distribute(secret, target))

        except Exception as e:
            LOGGER.error(
                "Failed to distribute key '{}' for provider '{}'!".format(
                    target['key'],
                    target['provider']
                )
            )
            return self._fail(e)

    @staticmethod
    def _default_response(status, action=None, msg=None, value=None):
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

    @staticmethod
    def _fail(msg, action=None, value=None):
        return Keydra._default_response('fail', action=action, value=value, msg=str(msg), )

    @staticmethod
    def _success(value, action=None):
        return Keydra._default_response('success', action=action, value=value)

    @staticmethod
    def _partial_success(value, msg, action=None):
        return Keydra._default_response('partial_success', action=action, value=value, msg=msg)

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

            for dresult in result.get('distribute_secret', {}).get('value', []):
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
