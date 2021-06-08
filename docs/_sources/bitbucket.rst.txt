.. _setup_bitbucket:

=======================
Initial Bitbucket Setup
=======================

To use Bitbucket for your config source, read on. If needed, you
can `create a free account here. <https://id.atlassian.com/signup?application=bitbucket>`_

Setup a configuration repository
================================

1.  Create a new private repository in Bitbucket. Let's call it `KeydraConfiguration`.

.. image:: _static/create_repo.png
    :width: 400px
    :alt: Create a Bitbucket repository

2.  Clone your new repo locally. Click the *Clone* button at the top right of your new repo's `Source` page, and paste into your terminal.
    
    Note: You may need to setup an SSH key for this, `see here for help if needed. <https://support.atlassian.com/bitbucket-cloud/docs/set-up-an-ssh-key/>`_

.. code-block:: bash

    git clone git@bitbucket.org:<your BB username>/keydraconfiguration.git
    cd keydraconfiguration

Create app credentials
======================

1.  Create App password for your Bitbucket user. Click your user avatar in the bottom left corner, then `Personal settings` > `App passwords`.
    Click the blue `Create app password` button.

.. image:: _static/create_app_password.png
    :width: 400px
    :alt: Create a App password

2.  Call the App password `keydra`, and minimum permissions. Click `Create`.

.. image:: _static/perms_app_password.png
    :width: 400px
    :alt: Configure App password permissions

3. You'll be shown a password, which you'll only see once! In another tab, login to the AWS Console and navigate to the `Secrets Manager` service.

4. Click the orange `Store a new secret` button.

.. image:: _static/store_secret.png
    :width: 400px
    :alt: Store a secret

5. Choose a secret type of `Other type of secrets`, and add a plaintext secret as follows (substituting your details).

.. code-block:: json

    {
    "password": "<the password from step 3>",
    "username": "<your bb username>"
    }

6.  You can leave encryption settings as default, or update to your needs. Click `Next`.

7.  Call your secret `keydra/bitbucket`, and add a tag of 'managedby'='keydra'. Click `Next`.

8.  Auto rotation is not required (Keydra will do this), so just click `Next` on the next screen, then `Store` on the one after.
