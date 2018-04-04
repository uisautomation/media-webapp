#!/usr/bin/env sh
set -xe
hydra migrate sql $DATABASE_URL
exec hydra host --dangerous-auto-logon --dangerous-force-http
