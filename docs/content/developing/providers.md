---
title: "Providers"
date: 2022-02-05T14:03:08+11:00
draft: false
---

*Providers* make the magic happen. As of today they have 2 responsibilities:

* [rotation](#rotate) (which depending on the provider, can also be used to provision secrets)

* [distribution](#distribute)

... and implement the methods described in `keydra.providers.base`.
See the [provider documentation](../../providers) for more details on what's supported out of the box.

<a name="rotate"></a>
### Rotation

During the `rotate` phase, the provider will be invoked with a description
(`dict`) of a secret.

So in the example below where `secrets.yaml` has:

```yaml
    secret_identifier:
    description: Some description for the secret
    key: key_identifier
    provider: provider_type
    rotate: nightly
    distribute:
        - ...
```

The rotate method will receive:

```json
    {
        "description": "Some description for the secret",
        "key": "key_identifier",
        "provider": "provider_type",
        "rotate": "nightly"
    }
```

Note that the `provider` attribute is what brought the config into your
provider to begin with.

From that moment on it is your responsibility to _rotate_ (whatever it means
to your provider) the secret described as `key_identifier`.

Something goes wrong, simply raise `keydra.exceptions.RotationException`.

All going well, return a `dict` containing the attributes of your secret
(including the secret bits, like password... don't worry it is safe and never
logged... unless you mess up).

<a name="distribute"></a>
### Distribution

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
