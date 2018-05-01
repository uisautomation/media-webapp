# Streaming Media Service Webapp

[![Build
Status](https://travis-ci.org/uisautomation/sms-webapp.svg?branch=master)](https://travis-ci.org/uisautomation/sms-webapp)
[![codecov](https://codecov.io/gh/uisautomation/sms-webapp/branch/master/graph/badge.svg)](https://codecov.io/gh/uisautomation/sms-webapp)

Documentation for developers, including a "getting started" guide, can be found
at https://uisautomation.github.io/sms-webapp.

## Short, short version

Firstly, [install docker-compose](https://docs.docker.com/compose/install/).
Then most tasks can be performed via the ``compose.sh`` script:

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

## Dockerfile configuration

The following environment variables need to be set when running the application
via Docker:

* DJANGO_SECRET_KEY
* DJANGO_DB_ENGINE, DJANGO_DB_HOST, DJANGO_DB_PORT, DJANGO_DB_PASSWORD, etc.
* JWPLATFORM_EMBED_PLAYER_KEY
* JWPLATFORM_API_KEY and JWPLATFORM_API_SECRET
* OAUTH2_CLIENT_ID and OAUTH2_CLIENT_SECRET

See the [Dockerfile](Dockerfile).
