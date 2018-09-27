#!/usr/bin/env bash
#
# Wrapper script to run manage.py in development. Arguments are passed directly
# to manage.py

# Exit on failure
set -e

# Change to this script's directory
cd "$( dirname "${BASH_SOURCE[0]}")"

# Execute manage.py, logging command used
set -x
exec ./compose.sh development run --rm development_app -- ./manage.py $@
