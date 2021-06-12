.. _cfg_providers:

======================
About Config Providers
======================

Config providers are a special type of Keydra provider, that can be the source of secrets and environments for Keydra to manage.

They must have an `accountusername` attribute, and a `load_config` method, which they use to bootstrap Keydra.

This special method is passed initial config values, which are built by Keydra from environment variables as can be seen in `docsrc/sample_template.yaml`.

.. code-block:: json

    {
        'accountusername': 'an_account',
        'secrets': {
            'repository': 'keydraconfiguration',
            'filetype': 'yaml',
            'path': 'config/secrets.yaml'
        },
        'environments': {
            'filetype': 'yaml',
            'repository': 'keydraconfiguration',
            'path': 'config/environments.yaml'
        }
    }

When distributing secrets to a code repo, the config accountusername will be used by default, unless over-ridden within the
config section of the distribution spec. For example, this distribution would use the gyrospectre organisation in Github:

.. code-block:: yaml

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

Whereas this spec overrides the default to use the `woot` org.

.. code-block:: yaml

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
