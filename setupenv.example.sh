# Template "setupenv.sh" file.
#
# Use this file to create a "setupenv.sh" file in the root of the repository
# which can be used to configure the environment with sensitive or
# local-specific values. Activate before running application as a developer
# via: "source setupenv.sh".
#
# THIS FILE IS ONLY OF USE DURING DEVELOPMENT. IT PLAYS NO ROLE IN DEPLOYMENT.

# Get these credentials by logging into the jwplatform dashboard and clicking
# the "API KEYS" link at the top-right of the Home screen.
export JWPLATFORM_API_KEY="your-api-key-here"
export JWPLATFORM_API_SECRET="your-api-secret-here"

# Find this by logging into the jwplatform dashboard and going to "Players" ->
# "Blank Embed Player". The player key is visible in the URL.
export JWPLATFORM_EMBED_PLAYER_KEY="player-key-for-embed"
