FROM uisautomation/python:django

# Do everything relative to /usr/src/app which is where we install our
# application.
WORKDIR /usr/src/app

# Clone latest lookupproxy source
RUN \
	git clone https://github.com/uisautomation/lookupproxy /usr/src/app && \
	pip install -r requirements.txt && \
	pip install -r requirements_developer.txt

# Copy startup script
ADD ./start-devserver.sh ./wait-for-it.sh /tmp/

# By default, use the Django development server to serve the application and use
# developer-specific settings.
#
# *DO NOT DEPLOY THIS TO PRODUCTION*
ENV DJANGO_SETTINGS_MODULE lookupproxy.settings_developer
ENTRYPOINT ["/tmp/wait-for-it.sh", "lookupproxy-db:5432", "--", "/tmp/start-devserver.sh"]
