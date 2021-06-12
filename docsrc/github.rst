.. _setup_github:

====================
Initial Github Setup
====================

To use Github for your config source, read on.

Setup a configuration repository
================================

1.  Create a new private repository in Github. Let's call it `KeydraConfiguration`.

2.  Clone your new repo locally. Click the *Clone* button in your new repo, and paste into your terminal.
    
.. code-block:: bash

    git clone git@github.com:<your Github org or username>/keydraconfiguration.git
    cd keydraconfiguration


Create a Personal Access Token
==============================

1. From your repository in your browser, click `Settings` from your profile avatar in the top right corner.

2. Choose `Developer settings` > `Personal access tokens` > `Generate new token`.

3. Give the token a name, all `repo` permissions, then click `Generate token`.

.. image:: _static/pat.png
    :width: 400px
    :alt: Personal access token creation

4. You'll be shown a password, which you'll only see once! In another tab, login to the AWS Console and navigate to the `Secrets Manager` service.

5. Click the orange `Store a new secret` button.

.. image:: _static/store_secret.png
    :width: 400px
    :alt: Store a secret

6. Choose a secret type of `Other type of secrets`, and add a plaintext secret as follows (substituting your details).

.. code-block:: json

    {
    "password": "<the token from step 4>",
    "username": "<your github username>"
    }

7.  You can leave encryption settings as default, or update to your needs. Click `Next`.

8.  Call your secret `keydra/github`.

9.  Auto rotation is not required (Keydra will do this), so just click `Next` on the next screen, then `Store` on the one after.
