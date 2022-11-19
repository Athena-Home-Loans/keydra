import unittest

from datetime import datetime
from datetime import timedelta

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry


@exponential_backoff_retry(1, delay=0.1, max_random=0.01)
def _failing_function():
    raise Exception('Boom')


@exponential_backoff_retry(1, delay=1)
def _passing_function():
    return True


class Dummy(object):
    @exponential_backoff_retry(1, delay=0.1, max_random=0.01)
    def fail(self):
        raise Exception('Boom')

    def success(self):
        return True


class TestBaseProvider(unittest.TestCase):
    def test_exponential_backoff_retry_successful_call(self):
        self.assertEqual(_passing_function(), True)

        dummy = Dummy()

        self.assertEqual(dummy.success(), True)

    def test_exponential_backoff_retry_failing_call_in_function(self):
        starttime = datetime.now()

        with self.assertRaises(Exception):
            _failing_function()

        self.assertGreaterEqual(
            datetime.now() - starttime, timedelta(seconds=0.1)
        )

    def test_exponential_backoff_retry_failing_call_in_method(self):
        starttime = datetime.now()

        with self.assertRaises(Exception):
            dummy = Dummy()

            dummy.fail()

        self.assertGreaterEqual(
            datetime.now() - starttime, timedelta(seconds=0.1)
        )

    def test_redact_result_default_keys_get_redacted(self):
        original_result = {
            'some_key': 'some_value',
            'value': {
                'provider': 'test-provider',
                'key': 'test-key',
                'secret': 'test-secret',
                'password': 'test-password',
            }
        }
        redacted_result = BaseProvider.redact_result(original_result, {})
        self.assertNotEqual(redacted_result, original_result)
        self.assertEqual({
            'some_key': 'some_value',
            'value': {
                'provider': 'test-provider',
                'key': 'test-key',
                'secret': '***',
                'password': '***',
            }
        }, redacted_result)

    def test_validate_spec_base(self):
        class DummyA(BaseProvider):
            def rotate(self, spec):
                pass

            def distribute(self, secret, key):
                pass

            def load_config(self, config):
                pass

        dummy_a = DummyA()
        valid, _ = dummy_a.validate_spec({'provider': 'provider', 'key': 'key'})
        self.assertTrue(valid)
        invalid, msg = dummy_a.validate_spec({})
        self.assertFalse(invalid)

    def test_validate_spec_override(self):
        class DummyA(BaseProvider):
            def load_config(self, config):
                pass

            def rotate(self, spec):
                pass

            def distribute(self, secret, key):
                pass

            @classmethod
            def validate_spec(cls, spec):
                return True, 'It is alive'

        dummy_a = DummyA()
        _, msg = dummy_a.validate_spec(None)
        self.assertEqual(msg, 'It is alive')

    def test_pre_process_bypass(self):
        class DummyA(BaseProvider):
            def rotate(self, key):
                pass

            def distribute(self, secret, key):
                pass

            def load_config(self, config):
                pass

        spec = {'a': 'b'}
        resp = DummyA.pre_process_spec(spec, {})
        self.assertEqual(spec, resp)
