from keydra.clients.aws.cloudwatch import CloudwatchClient
from keydra.keydra import Keydra
import unittest

from unittest.mock import Mock, call
from unittest.mock import MagicMock
from unittest.mock import patch


CONFIG = [
    {
        'provider': 'IAM',
        'key': 'km_managed_api_user',
        'distribute': [
            {
                'provider': 'bitbucket',
                'key': 'DEV_AWS_ACCESS_ID',
                'source': 'key',
                'config': {
                    'account_username': 'acct_user',
                    'scope': 'account'
                }
            },
            {
                'provider': 'bitbucket',
                'key': 'DEV_AWS_SECRET_ACCESS_KEY',
                'source': 'secret',
                'config': {
                    'account_username': 'acct_user',
                    'scope': 'account'
                }
            }
        ]
    }
]


SUCCESS = [
    {
        'key': 'km_managed_api_user',
        'provider': 'iam',
        'secret_id': 'IAM::km_managed_api_user',
        'rotate_secret': {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'iam',
                'key': 'AKIAWZVM3HTIRM5XSNF3',
                'secret': '***'
            }
        },
        'distribute_secret': {
            'status': 'success',
            'value': [
                {
                    'status': 'success',
                    'value': {
                        'key': 'DEV_AWS_ACCESS_KEY_ID',
                        'provider': 'bitbucket',
                        'source': 'key',
                        'envs': ['*'],
                        'config': {
                            'scope': 'account'
                        }
                    }
                },
                {
                    'status': 'success',
                    'value': {
                        'key': 'DEV_AWS_SECRET_ACCESS_KEY',
                        'provider': 'bitbucket',
                        'source': 'secret',
                        'envs': ['*'],
                        'config': {
                            'scope': 'account'
                        }
                    }
                }
            ]
        }
    }
]


PARTIAL_SUCCESS = [
    {
        'key': 'km_managed_api_user',
        'provider': 'iam',
        'secret_id': 'IAM::km_managed_api_user',
        'rotate_secret': {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'iam',
                'key': 'AKIAWZVM3HTIRM5XSNF3',
                'secret': '***'
            }
        },
        'distribute_secret': {
            'status': 'partial_success',
            'value': [
                {
                    'status': 'success',
                    'value': {
                        'key': 'DEV_AWS_ACCESS_KEY_ID',
                        'provider': 'bitbucket',
                        'scope': 'account',
                        'source': 'key',
                        'envs': ['*']
                    }
                },
                {
                    'status': 'fail'
                }
            ]
        }
    }
]


FAIL = [
    {
        'secret_id': 'IAM::km_managed_api_user',
        'key': 'km_managed_api_user',
        'provider': 'iam',
        'rotate_secret': {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'iam',
                'key': 'AKIAWZVM3HTIRM5XSNF3',
                'secret': '***'
            }
        },
        'distribute_secret': {
            'status': 'partial_success',
            'value': [
                {
                    'status': 'fail',
                },
                {
                    'status': 'fail'
                }
            ]
        }
    }
]


class TestKeydra(unittest.TestCase):
    def setUp(self):
        self._cfg = MagicMock()
        self._kdra = Keydra(cfg=self._cfg, cw=MagicMock())

    @patch('keydra.loader.SECRETS_MANAGER.get_secret_value')
    @patch('keydra.providers.aws_iam.Client.rotate')
    @patch('keydra.providers.bitbucket.Client.distribute')
    def test___rotate_and_distribute(self, bbc_distribute: Mock,
                                     iamc_rotate: Mock, sm_gsv: Mock):
        sm_gsv.return_value = '{"username": "x", "password": "y"}'
        iamc_rotate.return_value = {
            'provider': 'iam',
            'key': 'somekey',
            'secret': 'somesecret'
        }
        CloudwatchClient.instance = MagicMock()
        self._cfg.load_secrets.return_value = CONFIG
        bbc_distribute.return_value = "distributed"

        result = self._kdra.rotate_and_distribute(
            run_for_secrets=CONFIG, rotate='nightly')

        self._kdra._cw.put_metric_data.assert_called()

        self.assertEqual(result[0]['rotate_secret']['status'], 'success')
        self.assertEqual(result[0]['distribute_secret']['status'], 'success')
        self._cfg.load_secrets.assert_called_once_with(
            secrets=CONFIG, rotate='nightly')

    def test__distribute_secret_failure(self):
        result = self._kdra._distribute_secret({
            'provider': 'IAM',
            'key': 'km_managed_api_user',
            'distribute': [
                {
                        'provider': 'bogus',
                }]
        },
            'secretval')

        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['msg'], 'Failed to distribute secrets')
        self.assertIn('Secret Provider for "bogus" is not available',
                      result['value'][0]['msg'])

    def test__default_response(self):
        self.assertTrue(isinstance(self._kdra._default_response('s'), dict))
        self.assertIn('status', self._kdra._default_response('s'))
        self.assertIn('msg', self._kdra._default_response('s', msg='m'))
        self.assertIn('action', self._kdra._default_response('s', action='a'))
        self.assertIn('value', self._kdra._default_response('s', value='v'))

    def test__success(self):
        self.assertTrue(isinstance(self._kdra._success('m'), dict))
        self.assertEqual(self._kdra._success('m')['status'], 'success')

    def test__partial_success(self):
        self.assertTrue(isinstance(
            self._kdra._partial_success('v', 'm'), dict))
        self.assertEqual(
            self._kdra._partial_success('v', 'm')['status'], 'partial_success'
        )

    def test__fail(self):
        self.assertTrue(isinstance(self._kdra._fail('m'), dict))
        self.assertEqual(self._kdra._fail('m')['status'], 'fail')

    def test__emit_spec_metrics(self):
        self._kdra._emit_spec_metrics(CONFIG)

        self._kdra._cw.put_metric_data.assert_called_once_with(
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
                    'Value': 1
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
                    'Value': 2
                },
            ],
            Namespace='Keydra'
        )

    def test__emit_result_metrics(self):
        self._kdra._emit_result_metrics(SUCCESS)
        self._kdra._emit_result_metrics(PARTIAL_SUCCESS)
        self._kdra._emit_result_metrics(FAIL)

        self._kdra._cw.put_metric_data.assert_has_calls(
            [
                call(
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
                            'Value': 1
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
                            'Value': 0
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
                            'Value': 2
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
                            'Value': 0
                        },
                    ],
                    Namespace='Keydra'
                ),
                call(
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
                            'Value': 1
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
                            'Value': 0
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
                            'Value': 1
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
                            'Value': 1
                        },
                    ],
                    Namespace='Keydra'
                ),
                call(
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
                            'Value': 1
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
                            'Value': 0
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
                            'Value': 0
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
                            'Value': 2
                        },
                    ],
                    Namespace='Keydra'
                )
            ]
        )
