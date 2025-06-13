#!/usr/bin/env bash
# This file should not need to change
# Please use EXTREME CAUTION when modifying this file.
# This script is used to install the CLI tool and its dependencies.

set -euo pipefail

OS=$(uname)
PFO_BASE=${HOME}/.pfo
K8S_LOCAL=${PFO_BASE}/k8s

# Let's exit out of the installation immediately if the OS is not supported.
if [[ "${OS}" != "Darwin" ]] && echo "Current OS is Mac only, your OS is not supported. Our apologies for the inconveinience." && exit 0

[[ "${OS}" == "Darwin" && -z "$(command -v python3)" ]] && echo '[ERROR] - Please ensure that "python3" is installed on the system.' && exit 1

echo "[INFO] - Installing the pfo-cli tool prerequisites..."
[[ ! -d ${PFO_BASE} ]] && mkdir ${PFO_BASE} # We need this directory to install some SHELL completions later.
[[ ! -d ${K8S_LOCAL} ]] && mkdir -p ${K8S_LOCAL} # We need this directory to install some SHELL completions later.

[[ -z "$(command -v python3 || true)" ]] && brew install python3
[[ -z "$(command -v gh || true)" ]] && brew install gh
[[ -z "$(command -v jq || true)" ]] && brew install jq
[[ -z $(command -v pipx || true) ]] && brew install pipx
[[ -z "$(command -v git || true)" ]] && brew install git
[[ -z "$(command -v kubernetes-cli || true)" ]] && brew install kubernetes-cli
[[ -z "$(command -v kustomize || true)" ]] && brew install kustomize
[[ -z "$(command -v kind || true)" ]] && brew install kind
[[ -z "$(command -v minikube || true)" ]] && brew install minikube
[[ -z "$(command -v argocd || true)" ]] && brew install argocd

# Here are some optional tools that you may want to install.
#[[ -z "$(command -v aws || true)" ]] && brew install awscli
#[[ -z "$(command -v eksctl || true)" ]] && brew install eksctl
#[[ -z "$(command -v k3d || true)" ]] && brew install k3d
#[[ -z "$(command -v skaffold || true)" ]] && brew install skaffold

PFO_ORG_REPO="PyFlowOps/k8s-installs"
PFO_K8S_SCRIPTS_LOCATION="refs/heads/main/deploy"

# We need to download the scripts from the k8s-installs repository.
curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/create_cluster.sh -o ${K8S_LOCAL}/create_cluster.sh
curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/kind-config.yaml -o ${K8S_LOCAL}/kind-config.yaml
curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/delete_all_clusters.sh -o ${K8S_LOCAL}/delete_all_clusters.sh
curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/delete_local_cluster.sh -o ${K8S_LOCAL}/delete_local_cluster.sh
curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/augment_config_file.sh -o ${K8S_LOCAL}/augment_config_file.sh

_PYTHON=$(command -v python3)
if [[ $(gh api /repos/PyFlowOps/pfo-cli/releases/latest | jq -r '.message') == *"Not Found"* ]]; then
  echo '[WARNING] - We cannot find a release for the pfo-cli...'
  echo '[ERROR] - Please ensure that the "PyFlowOps/pfo-cli" repository exists and is accessible.'
  exit 1
fi

_CLI_LATEST=$(gh api /repos/PyFlowOps/pfo-cli/releases/latest | jq -r '.tag_name')

[[ "${OS}" == "Darwin" ]] && brew install pipx
[[ "${OS}" == "Linux" ]] && $_PYTHON -m pip install --user pipx

pipx install git+https://github.com/PyFlowOps/pfo-cli.git@${_CLI_LATEST} --force

unset _PYTHON
unset OS
