FROM python:3.6-alpine

# Ensure packages are up to date and install some useful utilities
RUN apk update && apk add git vim postgresql-dev libffi-dev gcc musl-dev \
	libxml2-dev libxslt-dev

# From now on, work in the application directory
WORKDIR /usr/src/app

# Copy Docker configuration and install any requirements. We install
# requirements/docker.txt last to allow it to override any versions in
# requirements/requirements.txt.
ADD ./requirements/* ./requirements/
RUN pip install --no-cache-dir -r requirements/base.txt && \
	pip install --no-cache-dir -r requirements/docker.txt

# Copy the remaining files over
ADD . .

# Default environment for image.  By default, we use the settings module bundled
# with this repo. Change DJANGO_SETTINGS_MODULE to install a custom settings.
#
# You probably want to modify the following environment variables:
#
# DJANGO_DB_ENGINE, DJANGO_DB_HOST, DJANGO_DB_PORT, DJANGO_DB_USER
EXPOSE 8000
ENV \
	DJANGO_SETTINGS_MODULE=smswebapp.settings.docker \
	PORT=8000

# Use gunicorn as a web-server after running migration command
CMD gunicorn \
	--name smswebapp \
	--bind :$PORT \
	--workers 3 \
	--log-level=info \
	--log-file=- \
	--access-logfile=- \
	--capture-output \
	smswebapp.wsgi
