FROM python:3.6

# Do everything relative to /usr/src/app which is where we install our
# application.
WORKDIR /usr/src/app

# Install any explicit requirements
ADD requirements*.txt ./
RUN pip install -r ./requirements_developer.txt

# Copy the webapp source into the application root.
ADD . .

# We use "-e" here so that we may mount /usr/src/app as a volume and replace the
# python code with our own. This is useful when running this container as a
# developer, for example. See also the bundled docker-compose.yml and
# https://uis-smswebapp.readthedocs.io/en/latest/developer.html#docker-images
RUN pip install -e .

# By default, use the Django development server to serve the application and use
# developer-specific settings.
#
# *DO NOT DEPLOY THIS TO PRODUCTION*
ENV DJANGO_SETTINGS_MODULE smswebapp.settings_developer
ENTRYPOINT ["./manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
