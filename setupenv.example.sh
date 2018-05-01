# Template "setupenv.sh" file.
#
# Use this file to create a "setupenv.sh" file in the root of the repository
# which can be used to configure the environment with sensitive or
# local-specific values. Activate before running application as a developer
# via: "source setupenv.sh".
#
# THIS FILE IS ONLY OF USE DURING DEVELOPMENT. IT PLAYS NO ROLE IN DEPLOYMENT.

# Set settings module to a developer-friendly one.
export DJANGO_SETTINGS_MODULE=smswebapp.settings.developer

# Set secret key. This can be generated, e.g., by "pwgen 48 1".
export DJANGO_SECRET_KEY="..."

# Get these credentials by logging into the jwplatform dashboard and clicking
# the "API KEYS" link at the top-right of the Home screen.
export JWPLATFORM_API_KEY="your-api-key-here"
export JWPLATFORM_API_SECRET="your-api-secret-here"

# Find this by logging into the jwplatform dashboard and going to "Players" ->
# "Blank Embed Player". The player key is visible in the URL.
export JWPLATFORM_EMBED_PLAYER_KEY="player-key-for-embed"

# OAuth2 client id & secret which the API server uses to identify itself to the OAuth2 token introspection endpoint.
export OAUTH2_CLIENT_ID="your-oauth-client-id-here"
export OAUTH2_CLIENT_SECRET="your-oauth-client-secret-here"
