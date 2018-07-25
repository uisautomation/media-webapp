# How to configure CircleCI

CircleCI requires to be configured to hold the secrets used to push to Google Cloud.

## GCloud

We want to pull our containers to our Google Cloud project, so we need a service account with those persmissions
to be configured in our CircleCI project.

1. Read [CircleCI guide](https://circleci.com/docs/2.0/google-auth/) about how to configure Google Cloud Service
Accounts in CircleCI
2. Read [Google guide](https://cloud.google.com/container-registry/docs/access-control) about the permissions that
the Google Cloud Service Account need to have to push into a Google Cloud Container Registry. We will need to give
permission of "Storage Admin" role.
3. Read [Google guide](https://cloud.google.com/container-registry/docs/pushing-and-pulling) about how to push
container images to a Google Cloud Container Registry.
