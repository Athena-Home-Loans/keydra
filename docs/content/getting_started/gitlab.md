---
title: "Initial Gitlab Setup"
date: 2022-05-14T14:03:08+11:00
draft: false
---

To use Gitlab as your config source, read on.

## Setup a configuration repository

1.  Create a new repository in Gitlab. Let's call it `KeydraConfiguration`.

2.  Clone your new repo locally.

## Create a Personal Access Token   

1. Follow the instructions to create a personal access token. <https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html>

2. Log into to the AWS Console and navigate to the `Secrets Manager` service.

3. Click the orange `Store a new secret` button.

<img src="/keydra/media/store_secret.png" alt="Store a secret" width="70%" />

4. Choose a secret type of `Other type of secrets`, and add a plaintext secret as follows (substituting your details).

```json
    {
    "access_token": "<your gitlab personal access token>"
    }
```

5.  You can leave encryption settings as default, or update to your needs. Click `Next`.

6.  Call your secret `keydra/gitlab`.

7.  Auto rotation is not required (Keydra will do this), so just click `Next` on the next screen, then `Store` on the one after.
