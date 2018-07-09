#!/usr/bin/env sh
#
# Run a database migration and start the development server.
set -xe

cd /usr/src/app

python ./manage.py migrate

exec python ./manage.py runserver 0.0.0.0:8080
