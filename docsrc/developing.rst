
=================
Developing Keydra
=================

.. toctree::
   :maxdepth: 5

If you are coding something new, chances are you are adding or updating a client, a provider or *both*!

Providers
=========

*Providers* make the magic happen. As of today they have 2 responsibilities:

* :ref:`rotate <rotate>` (which depending on the provider, can also be used to provision secrets)

* :ref:`distribute <distribute>`

... and implement the methods described in `keydra.providers.base`.
See the :ref:`provider documentation <providers>` for more details on what's supported out of the box.

.. _rotate:

Rotation
~~~~~~~~

During the `rotate` phase, the provider will be invoked with a description
(`dict`) of a secret.

So in the example below where `secrets.yaml` has:

.. code-block:: yaml

    secret_identifier:
    description: Some description for the secret
    key: key_identifier
    provider: provider_type
    rotate: nightly
    distribute:
        - ...

The rotate method will receive:

.. code-block:: json

    {
        "description": "Some description for the secret",
        "key": "key_identifier",
        "provider": "provider_type",
        "rotate": "nightly"
    }


Note that the `provider` attribute is what brought the config into your
provider to begin with.

From that moment on it is your responsibility to _rotate_ (whatever it means
to your provider) the secret described as `key_identifier`.

Something goes wrong, simply raise `keydra.exceptions.RotationException`.

All going well, return a `dict` containing the attributes of your secret
(including the secret bits, like password... don't worry it is safe and never
logged... unless you mess up).

.. _distribute:

Distribution
~~~~~~~~~~~~

During the `distribute` phase, the provider will be invoked with 2 descriptions
(`dict`, `dict`):

1. *the secret* (recently rotated, containing the *secret* bits)
2. A description of a distribution point.

From that moment on it is your responsibility to _distribute_ (whatever it
means to your provider) the secrets.

Remember that the secret will come decorated with `provider`, so if you need
to be specific about how to consume from certain providers you can. BUT...
if that is happening you probably missed something as the description of a
distribution point should be self-explanatory and self-contained.

Clients
=======

*Clients* _commonly_ live in `keydra.clients` but you may be sourcing it
directly from somewhere else or have other aspirations... no judgement here.

Anyway... *Clients* are nothing but SDKs to facilitate (keep the code clean,
really) the development of *Providers*.

See the :ref:`client documentation <clients>` for more details on what's supported.

Contribution guidelines
=======================

Plain and simple... just cut a PR!

But not so fast!

* Work on a feature branch
* Make sure you have tests
* Did you drop coverage, be ready to discuss why
* Create a Pull Request:

1. Install deps

(virtual environment recommended)

.. code-block:: bash

    pip install -r requirements-dev.txt
    pip install -r src/requirements.txt

2. Testing

.. code-block:: bash

    nosetests

Please ensure tests are passing before creating a PR. We also ask you to be PEP8 compliant!

.. code-block:: bash

    flake8
