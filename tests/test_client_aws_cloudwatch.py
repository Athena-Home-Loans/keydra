import unittest

from keydra.clients.aws.cloudwatch import CloudwatchClient
from keydra.clients.aws.cloudwatch import timed

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch


class TestCloudwatchClient(unittest.TestCase):
    def test_is_a_true_singleton(self):
        session = MagicMock()

        c1 = CloudwatchClient.getInstance(session)
        c2 = CloudwatchClient.getInstance(session)

        self.assertEqual(c1, c2)

    def test_timed_decorator(self):
        with patch.object(CloudwatchClient, 'instance') as mk_ti:
            @timed('Dimension', specialise=True)
            def a(*args, **kwargs):
                return 'a'

            resp_a = a()
            resp_b = a({'provider': 'Beer'})

            self.assertEqual(resp_a, 'a')
            self.assertEqual(resp_b, 'a')

            # TODO: This 0 here is brittle and needs to be replaced.
            # Let's consider using 'freezegun' when we have a chance
            mk_ti.put_execution_time.assert_has_calls(
                [
                    call('Dimension', 0), call('Dimension_beer', 0)
                ]
            )

    def test_timed_decorator_gibberish(self):
        with patch.object(CloudwatchClient, 'instance'):
            @timed('Dimension', specialise=True)
            def a(*args, **kwargs):
                return 'a'

            try:
                a()
                a({'provider': 'Beer'})
                a({'provider': {'ohmy': 'multilevel'}})
                a({'provider': {'ohmy': 'multilevel'}}, {'with': 'multiarg'})
                a({}, {})
                a(None, None)
                a('string', None)
                a(None, 'string')
                a(True, False)
            except Exception as e:
                self.fail('timed decorator can NEVER fail: ', e)
