#!/usr/bin/env bash
# The script loads the legacy SMS statistics DB into the application DB defined by DJANGO_DB_*.
#
# Usage:
#
#   copy-legacy-stats.sh <stats_url>

STATS_URL=$1
[ -z "${STATS_URL}" ] && RELEASE="${APP_RELEASE_NAME}"
if [ -z "${STATS_URL}" ]; then
    echo "Error: you need to provide the stats URL."
    exit 1
fi

echo "${DJANGO_DB_HOST}:${DJANGO_DB_PORT}:${DJANGO_DB_NAME}:${DJANGO_DB_USER}:${DJANGO_DB_PASSWORD}" >~/.pgpass
chmod 0600 ~/.pgpass
curl -sLo /tmp/stats.sql.gz $1
psql -h "${DJANGO_DB_HOST}" -p "${DJANGO_DB_PORT}" -U "${DJANGO_DB_USER}" "${DJANGO_DB_NAME}" -1 -c "CREATE SCHEMA IF NOT EXISTS stats"
(
    gunzip -d -c /tmp/stats.sql.gz |
    # This is required because pg_dump on the SMS box is too old to support the --if-exists option.
    sed -e 's/^CREATE \(TABLE\|INDEX\) /\0IF NOT EXISTS /' |
    sed -e 's/^DROP \(TABLE\|INDEX\) /\0IF EXISTS /' |
    # Use ON_ERROR_STOP so that an error in the script does not spam the logs with further errors.
    psql -h "${DJANGO_DB_HOST}" -p "${DJANGO_DB_PORT}" -U "${DJANGO_DB_USER}" "${DJANGO_DB_NAME}" -v ON_ERROR_STOP=1 -1 -f -
)
