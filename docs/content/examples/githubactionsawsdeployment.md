---
title: "Github Actions AWS Deployment Credentials"
date: 2022-05-14T14:03:08+11:00
draft: false
---

Example to rotate an AWS IAM user password; then, using an access token from the AWS Secrets Manager secret located at `keydra/github`, encrypt the IAM user Id/password values and save them to secrets within the `my_repo`
repo of the `me` Github account.

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
```
