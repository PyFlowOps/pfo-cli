#!/usr/bin/env bash
# Copyright (c) 2025, PyFlowOps
set -eou pipefail

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO="${BASE}/.."

shopt -s expand_aliases

# Check if the pyproject.toml file exists in the repository
if [[ ! -f "${REPO}/pyproject.toml" ]]; then
    echo "[ERROR] - The pyproject.toml file not found in the repository: There is no app created, please create your application first."
    echo "[CRITICAL] - This repo needs a project, or to be managed with the pfo CLI."
    echo "[CRITICAL] - Please create a project using the pfo CLI, or manage this repo with the pfo CLI."
    exit 0
else
    echo "[INFO] - Under Construction: The pyproject.toml file found in the repository..."

    # Install Python dependencies using pip
    echo "[INFO] - Installing Python Dependencies..."
    ${REPO}/.python/bin/poetry install

    echo "[INFO] - Application Setup Complete!"
    exit 0
fi
