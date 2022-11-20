import boto3
import logging
import os

from functools import reduce

from keydra import loader
from keydra import logging as km_logging

from keydra.clients.aws.cloudwatch import CloudwatchClient

from keydra.config import KeydraConfig

from keydra.keydra import Keydra

km_logging.setup_logging(logging.INFO)


# Global variables are reused across execution contexts (if available)
SESSION = boto3.Session()

ENV_CONFIG_PREFIX = 'KEYDRA_CFG'

LOGGER = km_logging.get_logger()

CW = CloudwatchClient.getInstance(
    session=SESSION, region_name=loader.DEFAULT_REGION_NAME
)


def _merge_dicts(a, b, path=None):
    if path is None:
        path = []

    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                _merge_dicts(a[key], b[key], path + [key])
        else:
            a[key] = b[key]

    return a


def _load_env_config():
    '''
    Converts Keydra specific environment variables into a config dict.

    E.g.

    `KEYDRA_CFG_FIRSTLEVEL=firstlevel` becomes:

    ```
    {'firstlevel': 'firstlevel'}
    ```

    `KEYDRA_CFG_FIRST_A=firstA` + `KEYDRA_CFG_FIRST_B=firstB` becomes:

    ```
    {'first': {'a': 'firstA', 'b': 'firstB'}}
    ```
    '''
    config = {}
    slicer = len(ENV_CONFIG_PREFIX) + 1

    for var, value in os.environ.items():
        if not var.startswith(ENV_CONFIG_PREFIX):
            continue

        var = var[slicer:].lower()
        segments = var.split('_')

        segments.append(value)

        config = _merge_dicts(
            config,
            reduce(lambda x, y: {y: x}, segments[::-1])
        )

    return config


def _load_keydra_config():
    return KeydraConfig(
        config=_load_env_config(),
        sts_client=SESSION.client('sts')
    )


def lambda_handler(event, context):
    '''
    AWS Lambda handler

    :param event: Event triggering this function
    :type event: :class:`dict`
    :param context: Lambda Context runtime methods and attributes
    :type context: :class:`object`

    `context` attributes
    ------------------

    context.aws_request_id: :class:`str`
        Lambda request ID
    context.client_context: :class:`object`
        Additional context when invoked through AWS Mobile SDK
    context.function_name: :class:`str`
        Lambda function name
    context.function_version: :class:`str`
        Function version identifier
    context.get_remaining_time_in_millis: :function:
        Time in milliseconds before function times out
    context.identity:
        Cognito identity provider context when invoked through AWS Mobile SDK
    context.invoked_function_arn: :class:`str`
        Function ARN
    context.log_group_name: :class:`str`
        Cloudwatch Log group name
    context.log_stream_name: :class:`str`
        Cloudwatch Log stream name
    context.memory_limit_in_mb: :class:`int`
        Function memory

        https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    '''
    trigger = event.get('trigger', 'nightly')
    run_for_secrets = event.get('secrets', None)
    debug_mode = event.get('debug', False)
    batch_number = event.get('batch_number', None)
    number_of_batches = event.get('number_of_batches', None)

    if debug_mode:
        LOGGER.setLevel(logging.DEBUG)
        logging.getLogger('boto3').setLevel(logging.INFO)
        logging.getLogger('botocore').setLevel(logging.INFO)

    LOGGER.info(
        'Kicking of Keydra for the {} run. Secrets: {}'.format(
            trigger.upper(),
            ', '.join(run_for_secrets) if run_for_secrets else 'ALL'
        )
    )

    resp = Keydra(_load_keydra_config(), CW).rotate_and_distribute(
        run_for_secrets=run_for_secrets, rotate=trigger, batch_number=batch_number, number_of_batches=number_of_batches)

    LOGGER.info(
        {
            'message': 'Finished execution of Keydra for the {} run. '
            'Secrets: {}'.format(
                trigger.upper(),
                ', '.join(run_for_secrets) if run_for_secrets else 'ALL'
            ),
            'data': resp
        }
    )

    if any(r.get('rotate_secret') == 'fail' or
           r.get('distribute_secret') == 'fail' for r in resp):
        raise Exception(resp)

    return resp
