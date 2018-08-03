FROM python:3.7

# Do everything relative to /usr/src/app which is where we install our
# application.
WORKDIR /usr/src/app

# Add useful packages
RUN apt-get -y update && apt-get -y install postgresql-client

# Install any explicit developer requirements
ADD ./requirements/* ./requirements/
RUN pip install --upgrade -r ./requirements/developer.txt

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
