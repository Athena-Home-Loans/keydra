.. _providers:

.. toctree::
   :caption: Providers
   :maxdepth: 2

=========
Providers
=========

AWS AppSync
===========

*AWS Appsync* (declared as `appsync`): currently can only
`rotate` secrets.  Returns rotated
keys in the format:

.. code-block:: json

   {
      "provider": "aws_appsync",
      "key": "key",
      "secret": "secret"
   }

.. automodule:: keydra.providers.aws_appsync
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`AWS AppSync <client_appsync>`.

AWS IAM
=======

*AWS IAM* (declared as `iam`): can only `rotate` secrets (as it doesn't really
make sense for it to receive (via distribution) any secrets). Returns rotated
keys in the format:

.. code-block:: json

   {
      "provider": "iam",
      "key": "<AWS ACCESS KEY ID>",
      "secret": "<AWS ACCESS SECRET KEY>"
   }

.. automodule:: keydra.providers.aws_iam
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`AWS IAM <client_iam>`

AWS Secrets Manager
===================

*AWS SecretsManager* (declared as `secretsmanager`): currently can only
`distribute` secrets. `rotate` is only supported in conjunction with `bypass: true`
for retrieval of existing secrets for the purposes of distribution to respective
destinations.

`secretsmanager` is _greedy_ in other words, it will take all that is provided
by the `secret` and stick it into AWS SecretsManager. So no 1-1 mapping or
cherry picking fragments.

.. automodule:: keydra.providers.aws_secretsmanager
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`AWS Secrets Manager <client_secretsmanager>`.

Bitbucket
=========

*Bitbucket* (declared as `bitbucket`): can `distribute` secrets
to the following scopes:

* `account` (account-level env variables)
* `repository` (build-level or development-level env variables)
* `deployment` (deployment environment env variable)

In the future will also
support `rotate` keys as its own secrets should be rotated by Keydra.

`bitbucket` requires 1:1 mapping of the secret, this is done via `source`.

.. automodule:: keydra.providers.bitbucket
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`Bitbucket <client_bitbucket>`.

Cloudflare
==========

*Cloudflare* (declared as `cloudflare`): can `rotate` secrets. Requires a
token with the  *Can create tokens* permission in Cloudflare, registered under
`manage_tokens.secret` in SecretsManager. When invoked rotates all of the
tokens pertaining to that account and make their `ID` and `SECRET` available,
as per `<token_name>.key` and `<token_name>.secret`.

.. automodule:: keydra.providers.cloudflare
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`Cloudflare <client_cloudflare>`.

Contentful
==========
.. automodule:: keydra.providers.contentful
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`Contentful <client_contentful>`.

Qualys
======

Provides password rotation support for Qualys accounts. Only `rotate` has been implemented,
`distribution` is not (yet?) supported.

For a given secret specification, the `rotate` function fetches the contents of a AWS Secrets Manager
secret located at `keydra/qualys/<key>` (using the key from the spec), and changes the password of the user
specified on the Qualys platform. As Qualys does not permit a user to change their own password via API, the
secret spec needs to specify a second account to be used to make the change.

For example, for a secret spec of:

.. code-block:: yaml

    sample:
      description: API User
      key: api
      provider: qualys
      rotate: nightly
      config:
         rotatewith:
            key: keydra/qualys/backup
            provider: secretsmanager
      distribute:
      -
         key: keydra/qualys/api
         provider: secretsmanager
         source: secret
         envs:
            - prod

The provider will take an AWS Secrets Manager secret, located at `keydra/qualys/api`:

.. code-block:: json

   {
      "platform": "US3",
      "username": "apiuser",
      "password": "Ssh.Secret!",
   }

Then use the creds of the secret at `keydra/qualys/backup` (in Secrets Manager, as configured in the spec) to
connect to the Qualys API and change the password of the `apiuser` account. With the distribution setup in the
example, the new password will then be placed into Secrets Manager, replacing the password with the new one.

See https://www.qualys.com/platform-identification/ to identify which platform your instance is on.


.. automodule:: keydra.providers.qualys
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`Qualys <client_qualys>`.

Salesforce
==========

*Salesforce* (declared as `salesforce`): currently can only `rotate` secrets.
Please note that users need to be manually created in salesforce
before added here.

Sample secret spec:

.. code-block:: yaml

   key: salesforce_sample
   description: Salesforce Example
   custodians: your_team
   provider: salesforce
   rotate: nightly
   distribute:
   -
      key: keydra/salesforce/salesforce_sample
      provider: secretsmanager
      source: secret
      envs:
         - prod

The Secrets Manager entry format is as follows:

.. code-block:: yaml

   {
   "provider": "salesforce",
   "key": "my_sf_user",
   "secret": "my_sf_password",
   "token": "sf_token",
   "domain": "sf_domain"
   }

The field names can be customised via a `config` section in the spec, e.g.:

.. code-block:: yaml

   key: salesforce_sample
   description: Salesforce Example
   provider: salesforce
   config:
      user_field: SF_USERNAME
      password_field: SF_PASSWORD
      token_field: SF_TOKEN
      domain_field: SF_DOMAIN
   # ...

.. automodule:: keydra.providers.salesforce
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`Salesforce <client_salesforce>`.

Splunk
======

Provides password rotation and distribution support for Splunk. Rotation allows for Splunk account 
passwords to be rotated, while Distribute allows you to save passwords from other providers in Splunk
apps, like Qualys or AWS.

Rotation generates a new 32 character password (using AWS Secrets Manager) and changes the Splunk password
for the account corresponding to the "key" value in the secret. This change is made on all Splunk hosts defined
in the "hosts" key of the secret.

An example secret spec to rotate a Splunk user password and store in AWS Secrets Manager:

.. code-block:: yaml

   key: splunkuser
   description: Splunk Rotation Example
   custodians: your_team
   provider: splunk
   rotate: nightly
   hosts:
   - your.splunkhostname.com
   distribute:
   -
      key: keydra/splunk/splunkuser
      provider: secretsmanager
      source: secret
      envs:
         - prod

The Secrets Manager entry format is as follows:

.. code-block:: yaml

   {
   "provider": "splunk",
   "key": "splunkuser",
   "secret": "abcdefghijklmnopqrstuvwxyz1234567890"
   }

Distribution is a little more complex; configuring a Splunk App or Add-On with a service account to be
used by that app to connect to various data sources. Only one destination host can be specified; if you need to
send to more Splunk hosts you will need another distribution entry. The provider supports either Splunk storage
passwords or a more custom method of actually storing the password on Splunk - which one to use depends on the
destination Splunk TA/app. For example, the AWS app for Splunk uses the custom method, while the Qualys app uses
storage passwords.

The destination app must already be installed on the Splunk instance, though the config entry / storage password 
will be created if it doesn’t already exist.

.. list-table:: Splunk Provider Distribution Format
   :widths: 25 25 50
   :header-rows: 1

   * - Key
     - Type
     - Value
   * - key
     - String
     - The object to distribute to. Ignored/optional if we're saving to a Splunk storage password.
   * - provider
     - String
     - Always “splunk” for this provider.
   * - provider_secret_key
     - String
     - The credentials that should be used to authenticate to the Splunk API. In the code, this value will be
       prepended with `keydra/splunk/` to form the secret name in AWS Secrets Manager where the creds are stored.
   * - source
     - Dict
     - Used to pass through values from the secret being distributed - format is `splunk field`: `secret key`. In
       the example below, a field of "secret_key" will be used in the Splunk post, containing the value of the
       "secret" key.
   * - config
     - Dict
     - See below for details.
   * - env
     - List
     - Which environments to run Keydra from. Should match the environment where the secret is held in Secrets Manager.

In the `config` section:

.. list-table:: Config Format
   :widths: 25 25 50
   :header-rows: 1

   * - Key
     - Type
     - Value
   * - host
     - String
     - The Splunk host to configure. Only one destination host can be specified, if you need to distribute
       to more Splunk hosts you will need another distribution entry.
   * - app
     - String
     - Splunk App context to deploy to.
   * - appconfig
     - Dict
     - Used to add any values needed by this Add-On. All appconfig KV pairs will be passed to the Splunk call as is.
   * - path
     - String
     - Optional. Specifies the (case sensitive!) URL path to the configuration section to update. Omit this key to
       save to a splunk storage password instead.
   * - realm
     - String
     - Optional. If storage passwords are being used, the realm to use in the password. Defaults to blank.

An example, to rotate an IAM user and distribute it into the AWS app/TA of a Splunk instance:

.. code-block:: yaml

   key: km_managed_splunk
   description: Rotate an AWS Splunk integration account
   custodians: your_team
   provider: IAM
   rotate: nightly
   distribute:
   -
      key: aws_security
      provider: splunk
      provider_secret_key: provisioning_user
      source:
         key_id: key
         secret_key: secret
      config:
         app: Splunk_TA_aws
         appconfig:
           category: 1
           output_mode: json
         host: your.splunkhostname.com
         path: splunk_ta_aws_aws_account
      envs:
         - prod

What does this do? Keydra will rotate these IAM credentials, then use the Splunk credentials stored in an AWS Secrets
Manager secret, located at 'keydra/splunk/provisioning_user' to connect to Splunk. It will then post the key value
pairs in the `config/appconfig` section to the app specified (Splunk_TA_aws), mixing in the keys in the `source`
section after mapping them from the secret. As in, the `key` value from the IAM secret will be posted as `key_id`.

Note: The category 1 reference? This is the category of the account. '1' is AWS Global (not GovCloud).

If your app uses storage passwords (like the Qualys app), the distribution stanza would look more like:

.. code-block:: yaml

   -
   provider: splunk
   provider_secret_key: provisioning_user
   source:
      name: username
      password: password
   config:
      app: TA-QualysCloudPlatform
      appconfig:
         output_mode: json
      host: your.splunkhostname.com
   envs:
      - prod

.. automodule:: keydra.providers.splunk
   :members:
   :undoc-members:
   :private-members:


Uses client :ref:`Splunk <client_splunk>`.
