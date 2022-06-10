---
title: "IAM User to ingest AWS Logs into Splunk"
date: 2022-05-14T14:03:08+11:00
draft: false
---

Example to rotate the secrets for an IAM user in AWS daily, creating if the user does not exist.
Distribute to the AWS Add On of a Splunk instance, using Splunk credentials from Secrets Manager in `keydra/splunk/awssplunk`.

```yaml
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
```
