.. _examples:

========
Examples
========

IAM User to ingest AWS Logs into Splunk
=======================================

Rotate the secrets for an IAM user in AWS daily, creating if the user does not exist.
Distribute to the AWS Add On of a Splunk instance, using Splunk credentials from Secrets Manager in `keydra/splunk/awssplunk`.

.. code-block:: yaml

    aws_splunk_integration:
        key: keydra_awssplunk
        description: Rotate the AWS Splunk integration account in Splunk
        custodians: my_team
        provider: IAM
        rotate: nightly
        distribute:
        -
            key: aws_prod
            provider: splunk
            provider_secret_key: awssplunk
            source:
                key_id: key
                secret_key: secret
            config:
                app: Splunk_TA_aws
                appconfig:
                    category: 1
                    output_mode: json
                host: splunk.mydomain.int
                path: splunk_ta_aws_aws_account
            envs:
                - prod

Salesforce Service Account
==========================

Rotate the secrets for a Salesforce user daily, distributing the new password to Secrets Manager.

.. code-block:: yaml

    salesforce_user:
        key: sfuser-dev
        description: Secret for break glass access to Salesforce Prod
        custodians: sf_team
        provider: salesforce
        rotate: nightly
        distribute:
        -
            key: keydra/salesforce/sf-user
            provider: secretsmanager
            source: secret
            envs:
                - dev

Github Actions AWS Deployment Credentials
=========================================

Rotate an AWS IAM user password then, using an access token from the AWS Secrets Manager secret
located at `keydra/github`, encrypt the IAM user Id/password values and save them to secrets within the `my_repo`
repo of the `me` Github account.

.. code-block:: yaml

    sample:
        key: keydra_managed_sample
        description: A secret which exists in IAM
        custodians: my_team
        provider: IAM
        rotate: nightly
        distribute:
        -
            config:
                repository: my_repo
                account_username: me
                scope: repository
            envs:
                - dev
            key: AWS_ACCESS_KEY_ID
            provider: github
            source: key
        -
            config:
                repository: my_repo
                account_username: me
                scope: repository
            envs:
                - dev
            key: AWS_SECRET_ACCESS_KEY
            provider: github
            source: secret

Gitlab AWS Deployment Credentials
=================================

Rotate an AWS IAM user's AWS_SECRET_ACCESS_KEY; then, using an access token from the AWS Secrets Manager secret
located at `keydra/gitlab`, store the IAM user's AK/SAK values as CI/CD variables within the `group/infra/releases` repo.

.. code-block:: yaml

    sample:
        key: keydra_managed_sample
        description: A secret which exists in IAM
        custodians: my_team
        provider: IAM
        rotate: nightly
        distribute:
        -
            config:
                repository: group/infra/releases
                scope: repository
            envs:
                - '*'
            key: AWS_ACCESS_KEY_ID
            provider: gitlab
            source: key
        -
            config:
                repository: group/infra/releases
                scope: repository
            envs:
                - '*'
            key: AWS_SECRET_ACCESS_KEY
            provider: gitlab
            source: secret
