---
title: "Initial Bitbucket Setup"
date: 2022-05-14T14:03:08+11:00
draft: false
---

To use Bitbucket for your config source, read on. If needed, you can [create a free account here.](https://id.atlassian.com/signup?application=bitbucket)

## Setup a configuration repository

1.  Create a new private repository in Bitbucket. Let's call it `KeydraConfiguration`.

<img src="/keydra/media/create_repo.png" alt="Create a Bitbucket repository" width="50%" />

2.  Clone your new repo locally. Click the *Clone* button at the top right of your new repo's `Source` page, and paste into your terminal.
    
    Note: You may need to setup an SSH key for this, [see here for help if needed.](https://support.atlassian.com/bitbucket-cloud/docs/set-up-an-ssh-key/)

```bash
    git clone git@bitbucket.org:<your BB username>/keydraconfiguration.git
    cd keydraconfiguration
```

Create app credentials
======================

1.  Create App password for your Bitbucket user. Click your user avatar in the bottom left corner, then `Personal settings` > `App passwords`. Click the blue `Create app password` button.

<img src="/keydra/media/create_app_password.png" alt="Create a App password" width="40%" />

2.  Call the App password `keydra`, and minimum permissions. Click `Create`.

<img src="/keydra/media/perms_app_password.png" alt="Configure App password permissions" width="40%" />

3. You'll be shown a password, which you'll only see once! In another tab, login to the AWS Console and navigate to the `Secrets Manager` service.

4. Click the orange `Store a new secret` button.

<img src="/keydra/media/store_secret.png" alt="Store a secret" width="70%" />

5. Choose a secret type of `Other type of secrets`, and add a plaintext secret as follows (substituting your details).

```json
    {
    "password": "<the password from step 3>",
    "username": "<your bb username>"
    }
```

6.  You can leave encryption settings as default, or update to your needs. Click `Next`.

7.  Call your secret `keydra/bitbucket`.

8.  Auto rotation is not required (Keydra will do this), so just click `Next` on the next screen, then `Store` on the one after.
