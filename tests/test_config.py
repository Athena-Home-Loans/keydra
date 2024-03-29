import copy
import unittest

from keydra.config import KeydraConfig

from keydra.exceptions import ConfigException

from unittest.mock import MagicMock
from unittest.mock import patch


ENVS = {
    "dev": {
        "description": "AWS Development Environment",
        "type": "aws",
        "access": "dev",
        "id": "001122",
        "secrets": [
            "aws_deployments",
            "splunk",
            "aws_deployment_just_rotate",
            "cloudflare_canary",
            "okta_canary",
            "office365_adhoc",
        ],
    },
    "uat": {
        "description": "AWS UAT Environment",
        "type": "aws",
        "access": "uat",
        "id": "334455",
        "secrets": ["aws_deployments"],
    },
    "prod": {
        "description": "AWS Prod Environment",
        "type": "aws",
        "access": "production",
        "id": 667788,
        "secrets": ["aws_deployments"],
    },
    "control": {
        "description": "AWS Master Environment",
        "type": "aws",
        "access": "production",
        "id": 991122,
        "secrets": ["aws_deployments"],
    },
}


SECRETS = {
    "aws_deployments": {
        "key": "km_managed_api_user",
        "provider": "IAM",
        "rotate": "nightly",
        "distribute": [
            {
                "key": "KM_{ENV}_AWS_ACCESS_ID",
                "provider": "bitbucket",
                "source": "key",
                "envs": ["*"],
                "config": {"scope": "account"},
            },
            {
                "key": "KM_{ENV}_AWS_SECRET_ACCESS_KEY",
                "provider": "bitbucket",
                "source": "secret",
                "envs": ["*"],
                "config": {"scope": "account"},
            },
            {
                "key": "KM_MANAGED_AWS_ACCESS_ID",
                "provider": "bitbucket",
                "source": "key",
                "envs": ["dev"],
                "config": {"scope": "account"},
            },
            {
                "key": "KM_MANAGED_AWS_SECRET_ACCESS_KEY",
                "provider": "bitbucket",
                "source": "secret",
                "envs": ["dev"],
                "config": {"scope": "account"},
            },
        ],
    },
    "aws_deployment_just_rotate": {
        "key": "km_managed_just_rotate",
        "provider": "IAM",
        "rotate": "nightly",
    },
    "splunk": {"key": "splunk", "provider": "salesforce", "rotate": "monthly"},
    "cloudflare_canary": {
        "key": "cloudflare_canary_key",
        "provider": "cloudflare",
        "rotate": "canaries",
    },
    "okta_canary": {"key": "okta_canary_key", "provider": "okta", "rotate": "canaries"},
    "office365_adhoc": {
        "key": "control_secrets",
        "provider": "office365",
        "rotate": "adhoc",
    },
}


SECRETS_S = {
    "splunk": {
        "key": "splunk",
        "provider": "salesforce",
        "rotate": "monthly",
        "distribute": [{"provider": "secretsmanager", "envs": ["dev"]}],
    }
}


ENV_CONFIG = {
    "provider": "bitbucket",
    "config": {
        "account_username": "acct_user",
        "secrets": {
            "repository": "secrets_repo",
            "path": "secrets_path",
            "filetype": "secrets_filetype",
        },
        "environments": {
            "repository": "envs_repo",
            "path": "envs_path",
            "filetype": "envs_filetype",
        },
    },
}


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.client = KeydraConfig(config=ENV_CONFIG, sts_client=MagicMock())

    def test__dodgy_config(self):
        with self.assertRaises(ConfigException):
            KeydraConfig(config={}, sts_client=MagicMock())

        with self.assertRaises(ConfigException):
            KeydraConfig(config={"provider": {}}, sts_client=MagicMock())

    def test__validate_spec_environments(self):
        envs = copy.deepcopy(ENVS)
        secrets = copy.deepcopy(SECRETS)

        self.client._validate_spec(envs, secrets)

        envs["prod"].pop("type")

        with self.assertRaises(ConfigException):
            self.client._validate_spec(envs, secrets)

        envs = copy.deepcopy(ENVS)

        envs["prod"].pop("id")

        with self.assertRaises(ConfigException):
            self.client._validate_spec(envs, secrets)

        with self.assertRaises(ConfigException):
            secrets = copy.deepcopy(SECRETS)

            secrets["aws_deployments"]["distribute"][0]["envs"] = ["notanenv"]
            self.client._validate_spec(ENVS, secrets)

    def test__validate_spec_secrets(self):
        envs = copy.deepcopy(ENVS)
        secrets = copy.deepcopy(SECRETS)

        self.client._validate_spec(envs, secrets)

        secrets["aws_deployments"].pop("provider")

        with self.assertRaises(ConfigException):
            self.client._validate_spec(envs, secrets)

        secrets = copy.deepcopy(SECRETS)

        secrets["aws_deployments"].pop("key")

        with self.assertRaises(ConfigException):
            self.client._validate_spec(envs, secrets)

        secrets = copy.deepcopy(SECRETS)

        secrets["aws_deployments"]["distribute"][0].pop("provider")

        with self.assertRaises(ConfigException):
            self.client._validate_spec(envs, secrets)

    def test__guess_current_environment(self):
        sts_client_mock = MagicMock()
        kc = KeydraConfig(config=ENV_CONFIG, sts_client=sts_client_mock)

        sts_client_mock.get_caller_identity.return_value = {'Account': 334455}
        self.assertEquals(kc._guess_current_environment(ENVS), "uat")

        sts_client_mock.get_caller_identity.return_value = {'Account': 667788}
        self.assertEquals(kc._guess_current_environment(ENVS), "prod")

        sts_client_mock.get_caller_identity.return_value = {'Account': 999999}
        with self.assertRaisesRegex(ConfigException, 'No environment is mapped to AWS account 999999'):
            kc._guess_current_environment(ENVS)

    def test__filter(self):
        with patch.object(self.client, "_guess_current_environment") as mk_gce:

            mk_gce.return_value = "prod"
            filtered = self.client._filter(ENVS, SECRETS, rotate="nightly")
            self.assertEqual(len(filtered), 1)
            self.assertEqual(len(filtered[0]["distribute"]), 2)

            mk_gce.return_value = "dev"
            filtered = self.client._filter(ENVS, SECRETS, rotate="nightly")
            self.assertEqual(len(filtered), 2)
            self.assertEqual(filtered[0]["key"], "km_managed_api_user")
            self.assertEqual(len(filtered[0]["distribute"]), 4)

            mk_gce.return_value = "dev"
            filtered = self.client._filter(ENVS, SECRETS, requested_secrets=[], rotate="nightly")
            self.assertEqual(len(filtered), 2)
            self.assertEqual(filtered[0]["key"], "km_managed_api_user")
            self.assertEqual(len(filtered[0]["distribute"]), 4)

            mk_gce.return_value = "dev"
            filtered = self.client._filter(
                ENVS,
                SECRETS,
                requested_secrets=["aws_deployment_just_rotate"],
                rotate="nightly",
            )
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["key"], "km_managed_just_rotate")

            mk_gce.return_value = "dev"
            filtered = self.client._filter(ENVS, SECRETS, rotate="monthly")
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["key"], "splunk")

            mk_gce.return_value = "dev"
            filtered = self.client._filter(ENVS, SECRETS_S, rotate="monthly")
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["key"], "splunk")
            self.assertEqual(filtered[0]["distribute"][0]["provider"], "secretsmanager")

            mk_gce.return_value = "dev"
            filtered = self.client._filter(ENVS, SECRETS_S, rotate="adhoc", requested_secrets=["splunk"])
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["key"], "splunk")
            self.assertEqual(filtered[0]["distribute"][0]["provider"], "secretsmanager")

            mk_gce.return_value = "dev"
            filtered = self.client._filter(ENVS, SECRETS, rotate="canaries")
            self.assertEqual(len(filtered), 2)
            self.assertEqual(filtered[0]["key"], "cloudflare_canary_key")
            self.assertEqual(filtered[1]["key"], "okta_canary_key")

    @patch("keydra.loader.build_client")
    def test_load_secret_specs(self, mk_bc):
        with patch.object(self.client, "_filter") as mk_fba:
            with patch.object(self.client, "_validate_spec") as mk_vc:
                self.client.load_secrets()

                mk_bc.assert_called_once_with(ENV_CONFIG["provider"], None)
                mk_fba.assert_called()
                mk_vc.assert_called()

    def test__filter_no_batch_size(self):
        all_secrets = {}
        envs = {"dev": {"secrets": []}}

        with patch.object(self.client, "_guess_current_environment") as mk_gce:
            mk_gce.return_value = "dev"

            filtered_secrets = self.client._filter(envs, all_secrets, rotate="nightly")

            assert len(filtered_secrets) == len(all_secrets)

    def test_filter_nightly_with_invalid_batch_input(self):
        # test parameters are number of batches, batch number
        invalid_integer_exception_regex = r"batch number -?\d+ of number of batches -?\d+ are not valid numbers"
        invalid_type_exception_regex = r"batch number .* or number of batches .* is not an integer"
        batch_parameters = [
            (0, 0, invalid_integer_exception_regex),  # zero batches
            (2, 2, invalid_integer_exception_regex),  # 2 batches, trying to fetch batch number 2, only 0,1 are valid
            (2, 4, invalid_integer_exception_regex),  # 2 batches, trying to fetch a batch number that is out pf range
            (1, -1, invalid_integer_exception_regex),  # negative batch number
            (-1, 1, invalid_integer_exception_regex),  # negative number of batches
            (-1, -1, invalid_integer_exception_regex),  # double negative
            ("str", 0, invalid_type_exception_regex),  # string number of batches
            (1, "str", invalid_type_exception_regex),  # string batch number
            ("str", "str2", invalid_type_exception_regex),  # double string
            (0.234, 0, invalid_type_exception_regex),  # float number of batches
            (3, 0.523, invalid_type_exception_regex),  # float batch number
        ]
        for (number_of_batches, batch_number, exception_regex) in batch_parameters:
            with self.subTest(
                f"testing failure for number of batches {number_of_batches}, batch number {batch_number}"
            ):
                all_secrets = {}
                envs = {"dev": {"secrets": []}}

                for i in range(1, 10):
                    secret_id = "secret" + str(i)
                    all_secrets[secret_id] = {
                        "key": secret_id,
                        "provider": "IAM",
                        "rotate": "nightly",
                    }

                with patch.object(self.client, "_guess_current_environment") as mk_gce:
                    mk_gce.return_value = "dev"
                    with self.assertRaisesRegex(Exception, expected_regex=exception_regex):
                        self.client._filter(
                            envs,
                            all_secrets,
                            rotate="nightly",
                            batch_number=batch_number,
                            number_of_batches=number_of_batches,
                        )

    def test_filter_batch_runs(self):
        """
        test parameters in list
        number of secrets,
        number of batches,
        batch number,
        expected number of filtered secrets,
        secret in first element
        :return:
        """
        batch_paramters = [
            (5, 1, 0, 5, "secret1"),  # single batch
            (4, 2, 0, 2, "secret1"),  # 2 batches, even number of secrets
            (5, 2, 1, 2, "secret4"),  # 2 batches, odd number of secrets
            (10, 3, 1, 4, "secret5"),  # 3 batches, get middle batch
            (10, 3, 0, 4, "secret1"),  # 3 batches, get first batch
            (10, 3, 2, 2, "secret9"),  # 3 batches, get last batch
        ]
        for (
            number_of_secrets,
            number_of_batches,
            batch_number,
            filtered_secrets_len,
            expected_first_secret,
        ) in batch_paramters:
            with self.subTest(
                f"testing for {number_of_secrets} secrets, batch number {batch_number} of {number_of_batches}"
            ):
                all_secrets = {}
                envs = {"dev": {"secrets": []}}

                for i in range(1, number_of_secrets + 1):
                    secret_id = "secret" + str(i)
                    all_secrets[secret_id] = {
                        "key": secret_id,
                        "provider": "IAM",
                        "rotate": "nightly",
                    }
                    all_secrets[secret_id][secret_id] = "for assertion"
                    envs["dev"]["secrets"].append(str(secret_id))

                with patch.object(self.client, "_guess_current_environment") as mk_gce:
                    mk_gce.return_value = "dev"
                    filtered_secrets = self.client._filter(
                        envs,
                        all_secrets,
                        rotate="nightly",
                        batch_number=batch_number,
                        number_of_batches=number_of_batches,
                    )
                    # should be a 3 - 2 split so batch number 0 should have 3 and number 1 should have 2
                    assert len(filtered_secrets) == filtered_secrets_len
                    assert expected_first_secret in filtered_secrets[0]

    def test_filter_no_secrets_run(self):
        all_secrets = {}
        envs = {"dev": {"secrets": []}}

        with patch.object(self.client, "_guess_current_environment") as mk_gce:
            mk_gce.return_value = "dev"
            filtered_secrets = self.client._filter(envs, all_secrets, rotate="nightly")
            assert len(filtered_secrets) == 0

    def test_filter_no_secrets_batch_run(self):
        number_of_batches = 2
        batch_number = 0
        all_secrets = {}
        envs = {"dev": {"secrets": []}}

        with patch.object(self.client, "_guess_current_environment") as mk_gce:
            mk_gce.return_value = "dev"
            filtered_secrets = self.client._filter(
                envs,
                all_secrets,
                rotate="nightly",
                batch_number=batch_number,
                number_of_batches=number_of_batches,
            )
            assert len(filtered_secrets) == 0
