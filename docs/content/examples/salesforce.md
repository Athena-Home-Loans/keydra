---
title: "Salesforce Service Account"
date: 2022-05-14T14:03:08+11:00
draft: false
---

Example to rotate the secrets for a Salesforce user daily, distributing the new password to Secrets Manager.

```yaml
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
```
