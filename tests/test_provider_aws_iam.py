from typing import FrozenSet
import unittest

from botocore.exceptions import ClientError

from datetime import datetime
from datetime import timedelta

from keydra.providers import aws_iam

from keydra.exceptions import DistributionException

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch


IAM_SECRET = {
    'key': 'secret_key',
    'secret': 'secret_secret',
    'provider': 'iam'
}

SM_DEST = {
    'key': 'secret_name',
    'provider': 'secretsmanager'
}


class TestProviderAWSIAM(unittest.TestCase):
    def test_redact_result(self):
        result = {
            'status': 'success',
            'action': 'rotate_secret',
            'value': {
                'provider': 'iam',
                'key': 'KEY_ID',
                'secret': 'THIS_IS_SECRET'
            }
        }

        r_result = aws_iam.Client.redact_result(result)
        r_value = r_result['value']['secret']

        self.assertNotEqual(r_value, 'THIS_IS_SECRET')

    def test__fetch_access_key(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._fetch_access_keys('user')
        cli._client.list_access_keys.assert_called_once_with(UserName='user')

    def test__pick_best_candidate_just_one_key(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        keys = [
            {'AccessKeyId': 'KEY_ONE', 'Status': 'Active'},
        ]

        keys_by_id = {
            x['AccessKeyId']: x for x in keys
        }

        now = datetime.now()

        cli._client.get_access_key_last_used.side_effect = [
            {'AccessKeyLastUsed': {'LastUsedDate': now}},
        ]

        candidate = cli._pick_best_candidate(keys_by_id)

        cli._client.get_access_key_last_used.has_calls(
            [
                call(AccessKeyId='KEY_ONE'),
            ]
        )

        self.assertEqual(candidate['AccessKeyId'], 'KEY_ONE')

    def test__pick_best_candidate_one_inactive_key(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        keys = [
            {'AccessKeyId': 'KEY_ONE', 'Status': 'Inactive'},
            {'AccessKeyId': 'KEY_TWO', 'Status': 'Active'},
        ]

        keys_by_id = {
            x['AccessKeyId']: x for x in keys
        }

        now = datetime.now()

        cli._client.get_access_key_last_used.side_effect = [
            {'AccessKeyLastUsed': {'LastUsedDate': now}},
            {'AccessKeyLastUsed': {'LastUsedDate': now}},
        ]

        candidate = cli._pick_best_candidate(keys_by_id)

        cli._client.get_access_key_last_used.has_calls(
            [
                call(AccessKeyId='KEY_ONE'),
                call(AccessKeyId='KEY_TWO'),
            ]
        )

        self.assertEqual(candidate['AccessKeyId'], 'KEY_ONE')

    def test__pick_best_candidate_two_active_keys(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        keys = [
            {'AccessKeyId': 'KEY_ONE', 'Status': 'Active'},
            {'AccessKeyId': 'KEY_TWO', 'Status': 'Active'},
        ]

        keys_by_id = {
            x['AccessKeyId']: x for x in keys
        }

        now = datetime.now()
        now_plus = now + timedelta(hours=1)

        cli._client.get_access_key_last_used.side_effect = [
            {'AccessKeyLastUsed': {'LastUsedDate': now_plus}},
            {'AccessKeyLastUsed': {'LastUsedDate': now}},
        ]

        candidate = cli._pick_best_candidate(keys_by_id)

        cli._client.get_access_key_last_used.has_calls(
            [
                call(AccessKeyId='KEY_ONE'),
                call(AccessKeyId='KEY_TWO'),
            ]
        )

        self.assertEqual(candidate['AccessKeyId'], 'KEY_TWO')

    def test__pick_best_candidate_two_active_keys_one_never_used(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        keys = [
            {'AccessKeyId': 'KEY_ONE', 'Status': 'Active'},
            {'AccessKeyId': 'KEY_TWO', 'Status': 'Active'},
        ]

        keys_by_id = {
            x['AccessKeyId']: x for x in keys
        }

        now = datetime.now()

        cli._client.get_access_key_last_used.side_effect = [
            {'AccessKeyLastUsed': {}},
            {'AccessKeyLastUsed': {'LastUsedDate': now}},
        ]

        candidate = cli._pick_best_candidate(keys_by_id)

        cli._client.get_access_key_last_used.has_calls(
            [
                call(AccessKeyId='KEY_ONE'),
                call(AccessKeyId='KEY_TWO'),
            ]
        )

        self.assertEqual(candidate['AccessKeyId'], 'KEY_ONE')

    def test__create_access_key(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()
        cli._client.create_access_key.return_value = {
            'AccessKey': {
                'AccessKeyId': 'key_id',
                'SecretAccessKey': 'new_secret'
            }
        }

        creds = cli._create_access_key('user')

        cli._client.create_access_key.assert_called_once_with(UserName='user')
        self.assertEqual(creds['SecretAccessKey'], 'new_secret')

    def test__delete_access_key(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._delete_access_key('user', 'key_id')

        cli._client.delete_access_key.assert_called_once_with(
            UserName='user',
            AccessKeyId='key_id'
        )

    def test__update_access_key(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._update_access_key('user', 'key_id', False)
        cli._update_access_key('user', 'key_id', True)

        cli._client.update_access_key.assert_has_calls(
            [
                call(UserName='user', AccessKeyId='key_id', Status='Inactive'),
                call(UserName='user', AccessKeyId='key_id', Status='Active'),
            ]
        )

    def test__create_user_if_not_available_exists(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._create_user_if_not_available('user')

        cli._client.get_user.assert_called_once_with(UserName='user')
        cli._client.create_user.assert_not_called()

    def test__create_user_if_not_available_does_not_exist(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._client.get_user.side_effect = ClientError(
            error_response={},
            operation_name=''
        )

        cli._create_user_if_not_available('user')

        cli._client.get_user.assert_called_once_with(UserName='user')
        cli._client.create_user.assert_called_once_with(
            UserName='user',
            Tags=[{'Key': 'managedby', 'Value': 'keydra'}]
        )

    def test__create_user_with_tags(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._client.get_user.side_effect = ClientError(
            error_response={},
            operation_name=''
        )

        cli._create_user_if_not_available(
            'user', options={'tags': {'x': '1', 'y': '2'}})

        cli._client.create_user.assert_called_once_with(
            UserName='user',
            Tags=[
                {'Key': 'managedby', 'Value': 'keydra'},
                {'Key': 'x', 'Value': '1'},
                {'Key': 'y', 'Value': '2'},
            ]
        )

    def test__create_user_add_tags(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._client.get_user.return_value = {
            'User': {
                'UserName': 'bananas',
                'Tags': [
                    {'Key': 'a', 'Value': 'b'}
                ]
            }
        }

        cli._create_user_if_not_available(
            'user', options={'tags': {'x': '1', 'y': '2'}})

        cli._client.create_user.assert_not_called()
        cli._client.tag_user.assert_called_once_with(
            UserName='user',
            Tags=[
                {'Key': 'managedby', 'Value': 'keydra'},
                {'Key': 'x', 'Value': '1'},
                {'Key': 'y', 'Value': '2'},
            ]
        )

    def test__create_does_nothing_on_match(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._client.get_user.return_value = {
            'User': {
                'UserName': 'bananas',
                'Tags': [
                    {'Key': 'managedby', 'Value': 'keydra'}
                ]
            }
        }

        cli._create_user_if_not_available('user')

        cli._client.create_user.assert_not_called()
        cli._client.tag_user.assert_not_called()

    def test__update_user_group_membership_no_existing_groups(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._client.list_groups_for_user.return_value = {'Groups': []}

        cli._update_user_group_membership('usr', ['G1'])

        cli._client.add_user_to_group.assert_has_calls(
            [
                call(UserName='usr', GroupName='G1'),
            ],
            any_order=True
        )

    def test__update_user_group_membership_replacing_groups(self):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        cli._client.list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'G2'}]
        }

        cli._update_user_group_membership('usr', ['G1'])

        cli._client.add_user_to_group.assert_has_calls(
            [
                call(UserName='usr', GroupName='G1'),
            ],
            any_order=True
        )

        cli._client.remove_user_from_group.assert_called_once_with(
            UserName='usr', GroupName='G2'
        )

    @patch.object(aws_iam.Client, '_get_aws_account_id')
    def test__update_user_policies_not_current(self, gaad):
        provider = aws_iam.Client(session=MagicMock())
        provider._client = MagicMock()
        gaad.return_value = '12345'

        provider._client.list_attached_user_policies.return_value = {
            'AttachedPolicies': []}

        provider._update_user_policies('usr', frozenset({'test/my_policy'}))

        provider._client.attach_user_policy.assert_has_calls(
            [call(UserName='usr', PolicyArn='arn:aws:iam::12345:policy/test/my_policy')])

        provider._client.detach_user_policy.assert_not_called()

    @patch.object(aws_iam.Client, '_get_aws_account_id')
    def test__update_user_policies_not_expected(self, gaad):
        provider = aws_iam.Client(session=MagicMock())
        provider._client = MagicMock()
        gaad.return_value = '12345'

        provider._client.list_attached_user_policies.return_value = {
            'AttachedPolicies': [{'PolicyArn': 'arn:aws:iam::12345:policy/test/my_policy'}]}

        provider._update_user_policies('usr', frozenset())

        provider._client.detach_user_policy.assert_has_calls(
            [call(UserName='usr', PolicyArn='arn:aws:iam::12345:policy/test/my_policy')])

        provider._client.attach_user_policy.assert_not_called()

    @patch.object(aws_iam.Client, '_get_aws_account_id')
    def test__update_user_policies_current_expected(self, gaad):
        provider = aws_iam.Client(session=MagicMock())
        provider._client = MagicMock()
        gaad.return_value = '12345'

        provider._client.list_attached_user_policies.return_value = {
            'AttachedPolicies': [{'PolicyArn': 'arn:aws:iam::12345:policy/test/my_policy'}]}

        provider._update_user_policies('usr', frozenset({'test/my_policy'}))

        provider._client.detach_user_policy.assert_not_called()
        provider._client.attach_user_policy.assert_not_called()

    @ patch.object(aws_iam.Client, '_fetch_access_keys')
    @ patch.object(aws_iam.Client, '_pick_best_candidate')
    @ patch.object(aws_iam.Client, '_delete_access_key')
    @ patch.object(aws_iam.Client, '_update_access_key')
    @ patch.object(aws_iam.Client, '_update_user_group_membership')
    @ patch.object(aws_iam.Client, '_create_access_key')
    def test_rotate(
        self, mk_cak, mk_uugm, mk_uak, mk_dak, mk_pbc, mk_fak
    ):
        cli = aws_iam.Client(session=MagicMock())
        cli._client = MagicMock()

        keys = [
            {'UserName': 'U', 'AccessKeyId': 'KEY_ONE', 'Status': 'Inactive'},
            {'UserName': 'U', 'AccessKeyId': 'KEY_TWO', 'Status': 'Active'},
        ]

        keys_by_id = {
            x['AccessKeyId']: x for x in keys
        }

        mk_fak.return_value = keys_by_id
        mk_pbc.return_value = keys_by_id['KEY_TWO']
        mk_cak.return_value = {
            'AccessKeyId': 'KEY_ONE',
            'SecretAccessKey': 'new_secret'
        }

        creds = cli.rotate(
            {'key': 'U', 'secret': 'secret', 'config': {'groups': ['G']}}
        )

        mk_fak.assert_called_once_with('U')
        mk_dak.assert_called_once_with(user='U', key_id='KEY_TWO')
        mk_uak.assert_called_once_with(
            user='U', key_id='KEY_ONE', active=False
        )
        mk_uugm.assert_called_once_with('U', ['G'])
        mk_cak.assert_called_once_with('U')

        self.assertEqual(
            creds,
            {'provider': 'iam', 'key': 'KEY_ONE', 'secret': 'new_secret'}
        )

    def test_distribute(self):
        cli = aws_iam.Client(session=MagicMock())

        with self.assertRaises(DistributionException):
            cli.distribute(None, None)

    def test_validate_spec_valid(self):
        speci_valid = {
            'secret': 'shhhhhhh tell no one',
            'key': 'treasury',
            'provider': 'IAM',
            'rotate': 'nightly'
        }

        r_result = aws_iam.Client.validate_spec(speci_valid)
        self.assertEqual(r_result[0], True)

    def test_validate_spec_valid_groups(self):
        speci_valid = {
            'secret': 'shhhhhhh tell no one',
            'key': 'treasury',
            'config': {
                'groups': ['x', 'y']
            },
            'provider': 'IAM',
            'rotate': 'nightly'
        }

        r_result = aws_iam.Client.validate_spec(speci_valid)
        self.assertEqual(r_result[0], True)

    def test_validate_spec_invalid_groups(self):
        speci_valid = {
            'secret': 'shhhhhhh tell no one',
            'key': 'treasury',
            'config': {
                'groups': 'justonegroup'
            },
            'provider': 'IAM',
            'rotate': 'nightly'
        }

        r_result = aws_iam.Client.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)

    def test_validate_spec_valid_tags(self):
        speci_valid = {
            'secret': 'shhhhhhh tell no one',
            'key': 'treasury',
            'config': {
                'tags': {
                    'x': 'y'
                }
            },
            'provider': 'IAM',
            'rotate': 'nightly'
        }

        r_result = aws_iam.Client.validate_spec(speci_valid)
        self.assertEqual(r_result[0], True)

    def test_validate_spec_invalid_tags(self):
        speci_valid = {
            'secret': 'shhhhhhh tell no one',
            'key': 'treasury',
            'config': {
                'tags': 'nope'
            },
            'provider': 'IAM',
            'rotate': 'nightly'
        }

        r_result = aws_iam.Client.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)

    def test_validate_spec_unsupported(self):
        speci_valid = {
            'secret': 'shhhhhhh tell no one',
            'key': 'treasury',
            'config': {
                'unsupported': 'nope'
            },
            'provider': 'IAM',
            'rotate': 'nightly'
        }

        r_result = aws_iam.Client.validate_spec(speci_valid)
        self.assertEqual(r_result[0], False)
