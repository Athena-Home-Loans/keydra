---
title: "About Config Providers"
date: 2022-05-14T14:03:08+11:00
draft: false
---

Config providers are a special type of Keydra provider, that can be the source of secrets and environments for Keydra to manage.

They must have an `accountusername` attribute, and a `load_config` method, which they use to bootstrap Keydra.

This special method is passed initial config values, which are built by Keydra from environment variables as can be seen in `docs/sample_template.yaml`.

```json
    {
        "accountusername": "an_account",
        "secrets": {
            "repository": "keydraconfiguration",
            "filetype": "yaml",
            "path": "config/secrets.yaml"
        },
        "environments": {
            "filetype": "yaml",
            "repository": "keydraconfiguration",
            "path": "config/environments.yaml"
        }
    }
```

When distributing secrets to a code repo, the config accountusername will be used by default, unless over-ridden within the
config section of the distribution spec. For example, this distribution would use the gyrospectre organisation in Github:

```yaml
    distribute:
        -
            config:
                repository: my_code
                scope: repository
            envs:
                - dev
            key: AWS_ACCESS_KEY_ID
            provider: github
            source: key
```

Whereas this spec overrides the default to use the `woot` org.

```yaml
    distribute:
        - 
            config:
                repository: my_code
                scope: repository
                account_username: woot
            envs:
                - dev
            key: AWS_ACCESS_KEY_ID
            provider: github
            source: key
```