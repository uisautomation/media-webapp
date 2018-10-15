# Use node container to build frontend app
FROM node:10 as frontend-builder

# Do everything relative to /usr/src/app which is where we install our
# application.
WORKDIR /usr/src/app

# Install packages and build frontend
ADD ./ui/frontend/ ./
RUN npm install && npm run build

# Use python alpine image to run webapp proper
FROM uisautomation/django:2.1-py3.7

# Ensure packages are up to date and install some useful utilities
RUN apk update && apk add git vim postgresql-dev libffi-dev gcc musl-dev \
	libxml2-dev libxslt-dev

# From now on, work in the application directory
WORKDIR /usr/src/app

# Copy Docker configuration and install any requirements. We install
# requirements/docker.txt last to allow it to override any versions in
# requirements/requirements.txt.
ADD ./requirements/* ./requirements/
RUN pip install --upgrade --no-cache-dir -r requirements/base.txt && \
	pip install --upgrade --no-cache-dir -r requirements/docker.txt

# Copy the remaining files over
ADD . .
COPY --from=frontend-builder /usr/src/app/build/ /usr/src/build/frontend/

# Default environment for image.  By default, we use the settings module bundled
# with this repo. Change DJANGO_SETTINGS_MODULE to install a custom settings.
#
# You probably want to modify the following environment variables:
#
# DJANGO_DB_ENGINE, DJANGO_DB_HOST, DJANGO_DB_PORT, DJANGO_DB_USER
EXPOSE 8000
ENV \
	DJANGO_SETTINGS_MODULE=mediawebapp.settings.docker \
	DJANGO_FRONTEND_APP_BUILD_DIR=/usr/src/build/frontend/ \
	PORT=8000

# Collect static files. We provide placeholder values for required settings.
RUN DJANGO_SECRET_KEY=placeholder ./manage.py collectstatic

# Use gunicorn as a web-server after running migration command
CMD gunicorn \
	--name mediawebapp \
	--bind :$PORT \
	--workers 3 \
	--log-level=info \
	--log-file=- \
	--access-logfile=- \
	--capture-output \
	mediawebapp.wsgi
