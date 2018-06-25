#!/usr/bin/env bash
#
# Wrapper script to run tox. Arguments are passed directly to tox.

# Exit on failure
set -e

# Change to this script's directory
cd "$( dirname "${BASH_SOURCE[0]}")"

# Execute tox runner, logging command used
set -x
exec ./compose.sh tox run --rm tox tox $@
