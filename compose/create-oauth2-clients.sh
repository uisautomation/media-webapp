#!/usr/bin/env bash
#
# Use Hydra command line client to create a client application.
#
# Create a client, "smswebapp", capable of requesting hydra.introspect and lookup:anonymous scopes.
#
set -xe

/tmp/wait-for-it.sh hydra:4444 -t 15

hydra connect \
  --id "${ROOT_CLIENT_ID}" --secret "${ROOT_CLIENT_SECRET}" \
  --url "http://hydra:4444/"

# Delete any existing clients. It is OK for these calls to fail if the
# corresponding clients did not exist
hydra clients delete smswebapp || echo "-- smswebapp not deleted"
hydra clients delete lookupproxy || echo "-- lookupproxy not deleted"

# Create smswebapp client which can request scopes to access the lookup proxy
# and to introspect tokens from hydra.
hydra clients create \
    --id smswebapp --secret smssecret \
    --grant-types client_credentials \
    --response-types token \
    --allowed-scopes lookup:anonymous,hydra.introspect

# Create lookupproxy client which can request scopes to access the lookup proxy
# using the implicit flow.
hydra clients create \
    --id lookupproxy \
    --grant-types implicit \
    --callbacks http://localhost:8080/static/lookupproxy/oauth2-redirect.html \
    --response-types token \
    --allowed-scopes lookup:anonymous

# We need to create a Hydra policy allowing the smswebapp to introspect tokens.
# Delete a policy if it is already in place and re-create it
hydra policies delete introspect-policy \
	|| echo "-- introspect-policy not deleted"

hydra policies create --actions introspect \
	--description "Allow all clients with hydra.introspect to instrospect" \
	--allow \
	--id introspect-policy \
	--resources "rn:hydra:oauth2:tokens" \
	--subjects "<.*>"
