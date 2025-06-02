#!/usr/bin/env bash
# This file should not need to change
# Please use EXTREME CAUTION when modifying this file.
# This script is used to install the CLI tool and its dependencies.

set -euo pipefail

# Let's ensure this file exists in the $HOME/.cli/.install
curl https://raw.githubusercontent.com/pyflowops/pfo-cli/refs/heads/main/pfo-cli/.install/installer.sh -o /tmp/installer.sh \
&& bash /tmp/installer.sh \
&& rm /tmp/installer.sh
