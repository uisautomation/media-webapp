#!/usr/bin/env bash
#
# Wrapper script to run services via docker-compose. Usage:
#
# ./compose.sh <config> [<args>...]
#
# Will be expanded into:
#
# docker-compose --file compose/base.yml --file compose/<config>.yml <args>...
#
# With <args>... defaulting to "up" if not specified.

config=$1
shift
args=${@:-up}

# Exit on failure
set -e

# Check some config was provided
if [ -z "${config}" ]; then
  echo "No configuration specified." >&2
  exit 1
fi

# Change to this script's directory
cd "$( dirname "${BASH_SOURCE[0]}")"

# Execute test runner, logging command used
set -x
exec docker-compose --file compose/base.yml --file compose/${config}.yml $args
