#!/usr/bin/env bash
#
# Use Hydra command line client to create a client application.
#
# Create a client, "smswebapp", capable of requesting hydra.introspect and lookup:anonymous scopes.
#
set -xe

# A convenient alias for calling hydra
function hydra() {
	docker-compose exec hydra hydra $@
}

# Delete any existing clients. It is OK for these calls to fail if the
# corresponding clients did not exist
hydra clients delete smswebapp || echo "-- smswebapp not deleted"

# Create smswebapp client which can request scopes to access the lookup proxy
# and to introspect tokens from hydra.
hydra clients create \
    --id smswebapp --secret smssecret \
    --grant-types client_credentials \
    --response-types token \
    --allowed-scopes lookup:anonymous,hydra.introspect

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
