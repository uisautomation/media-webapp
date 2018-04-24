# Streaming Media Service Webapp

[![Build
Status](https://travis-ci.org/uisautomation/sms-webapp.svg?branch=master)](https://travis-ci.org/uisautomation/sms-webapp)
[![codecov](https://codecov.io/gh/uisautomation/sms-webapp/branch/master/graph/badge.svg)](https://codecov.io/gh/uisautomation/sms-webapp)

Documentation for developers, including a "getting started" guide, can be found
at https://uisautomation.github.io/sms-webapp.

## Dockerfile configuration

The following environment variables need to be set when running the application
via Docker:

* DJANGO_SECRET_KEY
* DJANGO_DB_ENGINE, DJANGO_DB_HOST, DJANGO_DB_PORT, DJANGO_DB_PASSWORD, etc.
* JWPLATFORM_EMBED_PLAYER_KEY
* JWPLATFORM_API_KEY and JWPLATFORM_API_SECRET
* SMS_OAUTH2_CLIENT_ID and SMS_OAUTH2_CLIENT_SECRET
