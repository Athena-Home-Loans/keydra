---
title: "Gitlab AWS Deployment Credentials"
date: 2022-05-14T14:03:08+11:00
draft: false
---

Example to rotate an AWS IAM user's AWS_SECRET_ACCESS_KEY; then, using an access token from the AWS Secrets Manager secret
located at `keydra/gitlab`, store the IAM user's AK/SAK values as CI/CD variables within the `group/infra/releases` repo.

```yaml
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
```