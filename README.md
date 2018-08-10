# Streaming Media Service Webapp

[![CircleCI](https://circleci.com/gh/uisautomation/sms-webapp.svg?style=svg)](https://circleci.com/gh/uisautomation/sms-webapp)
[![codecov](https://codecov.io/gh/uisautomation/sms-webapp/branch/master/graph/badge.svg)](https://codecov.io/gh/uisautomation/sms-webapp)
[<img src="https://marker.io/vendor/img/logo/browserstack-logo.svg" height="20">](https://www.browserstack.com/)

Documentation for developers, including a "getting started" guide, can be found
at https://uisautomation.github.io/sms-webapp.

## Useful developer links

When a development environment is created via ``./compose.sh development up``,
the following endpoints are available:

* http://localhost:8000/ - the web application itself.
* http://localhost:3000/ - a version of the web application served from the
    create-react-app environment. Supports live reload of the UI when the
    underlying JavaScript changes.
* http://localhost:7000/ - a Swagger UI instance configured to point to the
    application's REST-ful API.
* http://localhost:6060/ - live generated documentation for the React components
    which form part of the UI.
* http://localhost:8080/ui - Swagger UI for a lookupproxy instance which can be
    used with an OAuth2 client called ``lookupproxy``

Additionally, endpoints for a mock hydra OAuth2 authorisation provider are
created. See [compose/base.yml](compose/base.yml) for the exposed ports for
those services.

## Short, short version

Firstly, [install docker-compose](https://docs.docker.com/compose/install/).

Secondly, copy the [example secrets.env file](secrets.env.in) to secrets.env and
populate it with the various secrets required.

Then, most tasks can be performed via the ``compose.sh`` script:

```bash
# Start development server
$ ./compose.sh development

# Start development server in background
$ ./compose.sh development up -d

# View logs
$ ./compose.sh development logs

# Stop the development server
$ ./compose.sh development down

# Run tests
$ ./compose.sh tox run --rm tox

# Start a server using the production Docker image
$ ./compose.sh production build
$ ./compose.sh production up -d
$ ./compose.sh production exec production_app ./manage.py migrate
```

Additionally the ``tox.sh`` and ``manage_development.sh`` wrapper scripts
provide convenient ways to run ``tox`` and management commands:

```bash
# Rebuild all testenvs
$ ./tox.sh -r

# Run only the flake8 tests
$ ./tox.sh -e flake8

# Run the migrate management command using the development images
$ ./manage_development.sh migrate

# Run tests and write coverage/documentation to build directory
$ ./compose.sh tox run -v $PWD:/tmp/workspace -e TOXINI_ARTEFACT_DIR=/tmp/workspace/build --rm tox
```

## Dockerfile configuration

The following environment variables need to be set when running the application
via Docker:

* DJANGO_SECRET_KEY
* DJANGO_DB_ENGINE, DJANGO_DB_HOST, DJANGO_DB_PORT, DJANGO_DB_PASSWORD, etc.
* JWPLATFORM_EMBED_PLAYER_KEY
* JWPLATFORM_API_KEY and JWPLATFORM_API_SECRET
* OAUTH2_CLIENT_ID and OAUTH2_CLIENT_SECRET

The following environment variables are optional:
* SMS_ENABLE_DEBUG_THIS_IS_DANGEROUS. Enables DJANGO DEBUG if set.
* DANGEROUS_DISABLE_HTTPS_REDIRECT. Disables HTTP to HTTPS redirect.

See the [Dockerfile](Dockerfile).

## Connecting the React world and the Django world

This section talks about the configuration required to get the React frontend
app to be served by the Django application retaining the ability to make use of
the live-reloading create-react-app server when necessary. It also outlines how
we build the frontend in production without littering the production container
with various node-related detritus.

The easiest requirement to satisfy is that the frontend at
http://localhost:3000/ works. We simply have a service in the docker-compose
configuration which runs "npm start" and exposes port 3000 to the host. We make
use of create-react-app's built in proxying support to proxy requests to the API
through to the Django development app.

Of course in production, we want the frontend to be served by the Django app and
we'd like to be able to test this when developing. To allow Django to serve the
app, we have some whitenoise configuration which arranges to serve files from a
frontend build directory (configured via a setting) from /. If a request to /foo
can be satisfied by a file from this directory, it is so otherwise the Django
app takes a turn to satisfy the request.

We have an additional docker-compose service which makes use of the watch script
we added to the frontend to watch for changes and build a new bundle of
HTML/JavaScript in a docker volume. This same volume is mounted in the Django
app container and is the directory whitenoise looks at.

The whitenoise configuration above is intended for use in production as well. We
arrange for the frontend production build files to be in a directory in the
production container and tell whitenoise to serve files from it.

The subtlety is in how those files get there.

We want the production image to remain small and so installing the entirety of
node, npm and the node_modules directory seems troublesome since we'll never
actually use them when running the container. Instead we make use of a useful
but little-known feature in Docker called a [multi-stage
build](https://docs.docker.com/develop/develop-images/multistage-build/). With
this feature a Dockerfile can actually use multiple stages and only keep the
last stage. We use this feature to compile the frontend JavaScript inside a node
container and then copy the compiled JavaScript *out* of that container and *in*
to the actual production container. This has the strong advantage that all of
the node-related stuff then gets thrown away after the image is built.

## Loading the legacy statistics schema

A current dump of the legacy statistics schema is available from a private URL.
This dump can be downloaded and imported to the development app using the
``copy-legacy-stats.sh`` script. Once the application is up, the script can be run as follows:

```bash
./compose.sh development exec development_app /tmp/copy-legacy-stats.sh <stats_url>
```

(the stats url can be discovered in the
[main deployment template of the media project's deployment repository](https://github.com/uisautomation/media-deploy/blob/master/deployment/deployment.py))
