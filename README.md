# Keydra #

Next level Secrets Management, without the price tag!

![Secrets Management for Humans](docs/static/keydra.png?raw=true "Keydra")

Keydra allows you to automatically rotate your secrets on a schedule you define. Since it's all automated, it's easy to rotate your service account and API keys much more frequently than you do today. Like, everyday!

This significanty decreases the period of time an attacker has to use compromised credentials, and lowers the risk for your organisation. Security FTW!

It runs as a Lambda function in AWS, and has two main functions:
1. Rotate: Change a secret 
2. Distribute: Store a secret 

These functions are called against *providers*, which are modular integrations with technology platforms. For each defined secret, you rotate on a single provider, but distribute to multiple providers.

Use case examples;

- Once a day, rotate/change an AWS IAM user password, and store in a BitBucket repository as a deployment variable to use in pipelines. *(rotate: AWS IAM, distribute: BitBucket)*

- Once a week, rotate/change a Salesforce user password, taking the current secret from AWS Secrets Manager and replacing with the new password once done. *(rotate: AWS SecretsManager, distribute: Salesforce, AWS SecretsManager)*

See [the documentation](https://athena-home-loans.github.io/keydra/) for a list of providers currently supported (the list is growing all the time!).

Need a new provider? It's easy to add one, cut a PR!

## Documentation

Check out the [documentation here](https://athena-home-loans.github.io/keydra/)!
