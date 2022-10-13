---
title: "Salesforce Marketing Cloud Service Account"
date: 2022-09-20T19:00:00+11:00
draft: false
---

Example to rotate the secrets for a Salesforce Marketing Cloud user daily, distributing the new password to Secrets Manager.

```yaml
    salesforce_marketing_cloud_user:
        key: sfuser-dev
        description: Secret for break glass access to Salesforce Prod
        custodians: sf_team
        provider: salesforce_marketing_cloud
        rotate: nightly
        distribute:
        -
            key: keydra/salesforce/sfmc-user
            provider: secretsmanager
            source: secret
            envs:
                - dev
```
