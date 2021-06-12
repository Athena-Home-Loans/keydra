import app
import unittest

from unittest.mock import MagicMock, patch


class TestLambda(unittest.TestCase):
    def setUp(self):
        pass

    @patch('keydra.keydra.Keydra.rotate_and_distribute')
    @patch('app._load_keydra_config')
    def test_lambda_handler_success(self, lkc, rad: MagicMock):
        rotation_result = [
            {'rotate_secret': 'success', 'distribute_secret': 'success'}]
        rad.return_value = rotation_result

        result = app.lambda_handler(event={'trigger': 'adhoc'}, context=None)

        self.assertEqual(result, rotation_result)

    @patch('keydra.keydra.Keydra.rotate_and_distribute')
    @patch('app._load_keydra_config')
    def test_lambda_handler_failure(self, lkc, rad):
        rotation_result = [
            {'rotate_secret': 'fail'}]
        rad.return_value = rotation_result

        with self.assertRaises(Exception):
            app.lambda_handler(event={'trigger': 'adhoc'}, context=None)
