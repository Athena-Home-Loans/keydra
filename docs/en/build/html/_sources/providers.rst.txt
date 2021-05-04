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

Salesforce
==========

*Salesforce* (declared as `salesforce`): currently can only
`rotate` secrets. Please note that users need to be manually created in salesforce
before added here.

.. automodule:: keydra.providers.salesforce
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`Salesforce <client_salesforce>`.

Splunk
======
.. automodule:: keydra.providers.splunk
   :members:
   :undoc-members:
   :private-members:

Uses client :ref:`Splunk <client_splunk>`.
