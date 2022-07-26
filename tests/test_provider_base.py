import unittest

from datetime import datetime
from datetime import timedelta

from keydra.providers.base import BaseProvider
from keydra.providers.base import exponential_backoff_retry


@exponential_backoff_retry(1, delay=1)
def _failing_function():
    raise Exception('Boom')


@exponential_backoff_retry(1, delay=1)
def _passing_function():
    return True


class Dummy(object):
    @exponential_backoff_retry(1, delay=1)
    def fail(self):
        raise Exception('Boom')

    @exponential_backoff_retry(1, delay=1)
    def success(self):
        return True


class TestBaseProvider(unittest.TestCase):
    def test_exponential_backoff_retry_successful_call(self):
        self.assertEqual(_passing_function(), True)

        dummy = Dummy()

        self.assertEqual(dummy.success(), True)

    def test_exponential_backoff_retry_failing_call(self):
        starttime = datetime.now()

        with self.assertRaises(Exception):
            _failing_function()

        self.assertGreaterEqual(
            datetime.now() - starttime, timedelta(seconds=1)
        )

        starttime = datetime.now()

        with self.assertRaises(Exception):
            dummy = Dummy()

            dummy.fail()

        self.assertGreaterEqual(
            datetime.now() - starttime, timedelta(seconds=1)
        )

    def test_redact_result_no_override(self):
        class ProviderWithDefaultRedactImplementation(BaseProvider):
            def load_config(self, config):
                pass

            def rotate(self, spec):
                pass

            def distribute(self, secret, dest):
                pass

        result = {'result': 'stuff'}

        self.assertEqual(result, ProviderWithDefaultRedactImplementation().redact_result(result))

    def test_redact_result_override(self):
        class ProviderThatRedactsResult(BaseProvider):
            def load_config(self, config):
                pass

            def rotate(self, spec):
                pass

            def distribute(self, secret, dest):
                pass

            @classmethod
            def redact_result(cls, result):
                result['result'] = '***'

                return result

        result = {'result': 'stuff'}
        r_result = ProviderThatRedactsResult().redact_result(result)

        self.assertNotEqual(r_result['result'], 'stuff')

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
