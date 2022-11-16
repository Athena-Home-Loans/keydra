---
title: "Batching Keydra Runs to avoid lambda timeout"
date: 2022-11-16T12:03:08+11:00
draft: false
---

Example to set up an AWS Event Rule in a serverless yaml file for a daily rotation splitting the runs into batches. 
This option was made available due to the 15-minute timeout cap on AWS Lambda. 
So if there were too many secrets such that the Keydra lambda function would time out during the rotation run, 
the batching option would be available to split the run into batches.

The example below splits the scheduled run into 2 batches 
and each schedule will run one half of the batch depending on which `batch_number` was given in the input.

`number_of_batches` represents the amount of groups the Keydra secrets will be split into

`batch_number` represents the which group is run. `batch_number` starts at 0 up to `number_of_batches` - 1.

I.e. If `number_of_batches: 2`, `batch_number: 0` will run the first half of the secrets 
and `batch_number: 1` will run the second half



```yaml
Resources:
  Keydra:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: keydra
      Description: Keydra - safe and lightweight management of secrets
      CodeUri: src/
      Handler: app.lambda_handler
      Runtime: python3.7
      MemorySize: 256
      Role: !Sub "<IAM Role Arn>"
      Environment:
        Variables:
          KEYDRA_CFG_PROVIDER: bitbucket, github or gitlab
          KEYDRA_CFG_CONFIG_ACCOUNTUSERNAME: <bb account name or github org name, unused for gitlab>
          KEYDRA_CFG_CONFIG_SECRETS_REPOSITORY: <secrets repo name>
          KEYDRA_CFG_CONFIG_SECRETS_REPOSITORYBRANCH: <repo branch to fetch secrets from (gitlab only)>
          KEYDRA_CFG_CONFIG_SECRETS_PATH: <path to secrets.yaml>
          KEYDRA_CFG_CONFIG_SECRETS_FILETYPE: yaml
          KEYDRA_CFG_CONFIG_ENVIRONMENTS_REPOSITORY: <environments repo name>
          KEYDRA_CFG_CONFIG_ENVIRONMENTS_REPOSITORYBRANCH: <repo branch to fetch environments from (gitlab only)>
          KEYDRA_CFG_CONFIG_ENVIRONMENTS_PATH: <path to environments.yaml>
          KEYDRA_CFG_CONFIG_ENVIRONMENTS_FILETYPE: yaml
      Events:
        KeydraNightlyFirstBatch:
          Type: Schedule
          Properties:
            Schedule: "cron(0 12 ? * * *)"
            Name: keydra-nightly-first-batch
            Description: Keydra nightly key rotation
            Input: '{"trigger": "nightly", "batch_number": 0, "number_of_batches: 2}'
            Enabled: true
        KeydraNightlySecondBatch:
          Type: Schedule
          Properties:
            Schedule: "cron(0 12 ? * * *)"
            Name: keydra-nightly-second-batch
            Description: Keydra nightly key rotation
            Input: '{"trigger": "nightly", "batch_number": 1, "number_of_batches: 2}'
            Enabled: true
```