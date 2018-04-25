FROM python:3.6-alpine

# Ensure packages are up to date and install some useful utilities
RUN apk update && apk add git vim postgresql-dev libffi-dev gcc musl-dev \
	libxml2-dev libxslt-dev bash

# Do everything relative to /usr/src/app which is where we install our
# application.
WORKDIR /usr/src/app

# Install any explicit developer requirements
ADD ./requirements/* ./requirements/
RUN pip install -r ./requirements/developer.txt

# The webapp source will be mounted here as a volume
VOLUME /usr/src/app

# Copy startup script
ADD ./compose/start-devserver.sh ./compose/wait-for-it.sh /tmp/

# By default, use the Django development server to serve the application and use
# developer-specific settings.
#
# *DO NOT DEPLOY THIS TO PRODUCTION*
ENV DJANGO_SETTINGS_MODULE smswebapp.settings_developer
ENTRYPOINT ["/tmp/wait-for-it.sh", "db:5432", "--"]
CMD ["/tmp/start-devserver.sh"]
