#!/usr/bin/env bash
# This file should not need to change
# Please use EXTREME CAUTION when modifying this file.
# This script is used to install the CLI tool and its dependencies.

set -euo pipefail

OS=$(uname)

[[ "${OS}" == "Linux" && -z "$(command -v python3)" ]] && echo '[ERROR] - Please ensure that "python3" is installed on the system.' && exit 1
[[ -z "$(command -v gh || true)" ]] && echo '[ERROR] - Please ensure that the "gh" CLI tool is installed on the system.' && exit 1
[[ -z "$(command -v jq || true)" ]] && echo '[ERROR] - Please ensure that the "jq" CLI tool is installed on the system.' && exit 1
[[ -z $(command -v pipx || true) ]] && echo "[ERROR] - Please ensure that the "pipx" CLI tool is installed on the system." && exit 1
[[ -z "$(command -v git || true)" ]] && echo '[ERROR] - Please ensure that the "git" tool is installed on the system.' && exit 1

_PYTHON=$(command -v python3)
if [[ $(gh api /repos/PyFlowOps/pfo-cli/releases/latest | jq -r '.message') == *"Not Found"* ]]; then
  echo '[WARNING] - We cannot find a release for the pfo-cli...'
  echo '[ERROR] - Please ensure that the "PyFlowOps/pfo-cli" repository exists and is accessible.'
  exit 0
fi

_CLI_LATEST=$(gh api /repos/PyFlowOps/pfo-cli/releases/latest | jq -r '.tag_name')

[[ "${OS}" == "Darwin" ]] && brew install pipx
[[ "${OS}" == "Linux" ]] && $_PYTHON -m pip install --user pipx

pipx install git+https://github.com/PyFlowOps/pfo-cli.git@${_CLI_LATEST} --force

unset _PYTHON
unset OS
